import os
import tempfile
import uuid
from pathlib import Path
import httpx
import asyncio
import logging
import moviepy.editor as mpy
import moviepy.video.fx.all as vfx
import numpy as np
import re
import json
import time
from difflib import SequenceMatcher
import whisper  # Import the whisper library directly

class VideoService:
    def __init__(self):
        # Create a temp directory for processing
        self.temp_dir = Path(tempfile.gettempdir()) / "brainrotify_video"
        os.makedirs(self.temp_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        # Pre-load Whisper model if available
        self.whisper_model = None
        try:
            self.logger.info("Loading Whisper model...")
            self.whisper_model = whisper.load_model("base") # Use base model by default for speed
            self.logger.info("Whisper model loaded successfully")
        except Exception as e:
            self.logger.warning(f"Could not load Whisper model: {str(e)}")
    
    async def create_video(self, image_paths, audio_path, script):
        """
        Create a video with multiple images and audio.
        
        Args:
            image_paths (list): List of paths to the background images
            audio_path (str): Path to the audio file
            script (str): The script text (used for generating captions)
            
        Returns:
            str: Path to the created video file
        """
        output_file = self.temp_dir / f"{uuid.uuid4()}.mp4"
        self.logger.info(f"Creating video at {output_file}")
        
        try:
            # Load audio and get its duration
            audio = mpy.AudioFileClip(audio_path)
            duration = audio.duration
            self.logger.info(f"Audio duration: {duration} seconds")
            
            if not image_paths:
                raise ValueError("No image paths provided")
            
            # Create base video clips with images
            if len(image_paths) == 1:
                # If only one image, use the original method
                image_clip = mpy.ImageClip(image_paths[0]).set_duration(duration)
                video = self._crop_to_aspect(image_clip, aspect=9/16)
                video = video.fadein(1).fadeout(1)
            else:
                # For multiple images, split the duration among them
                self.logger.info(f"Creating video with {len(image_paths)} images")
                segment_duration = duration / len(image_paths)
                clips = []
                
                for i, img_path in enumerate(image_paths):
                    # Create image clip
                    img_clip = mpy.ImageClip(img_path).set_duration(segment_duration)
                    # Crop to correct aspect ratio
                    img_clip = self._crop_to_aspect(img_clip, aspect=9/16)
                    
                    # Add fade effects (except for first and last clip which only need one fade)
                    if i == 0:
                        img_clip = img_clip.fadein(1).crossfadeout(1)
                    elif i == len(image_paths) - 1:
                        img_clip = img_clip.crossfadein(1).fadeout(1)
                    else:
                        img_clip = img_clip.crossfadein(1).crossfadeout(1)
                    
                    clips.append(img_clip)
                
                # Concatenate all clips
                video = mpy.concatenate_videoclips(clips, method="compose")
            
            # Generate caption timings using Whisper for accurate word timestamps
            self.logger.info("Generating caption timings using Whisper")
            caption_data = await self._get_whisper_timestamps(audio_path, script)
            self.logger.info(f"Generated {len(caption_data)} caption segments")
            
            # Add captions to the video
            video = self._add_captions_to_video(video, caption_data, audio)
            
            # Write the result to a file
            self.logger.info("Rendering video file...")
            video.write_videofile(
                str(output_file), 
                codec='libx264', 
                audio_codec='aac', 
                fps=24, 
                threads=4,
                logger=None  # Suppress MoviePy progress bars
            )
            
            self.logger.info(f"Video created successfully at {output_file}")
            return str(output_file)
        except Exception as e:
            self.logger.error(f"Error creating video: {str(e)}", exc_info=True)
            raise Exception(f"Error creating video: {str(e)}")
    
    async def _get_whisper_timestamps(self, audio_path, script):
        """
        Use Whisper to transcribe the audio and get accurate word timestamps,
        then align with the script using fuzzy matching.
        
        Args:
            audio_path (str): Path to the audio file
            script (str): The reference script
            
        Returns:
            list: Caption data with accurate word timing
        """
        try:
            # Try to use the Python Whisper library
            try:
                word_timings = await self._whisper_transcribe_python(audio_path)
                if word_timings:
                    return self._align_transcription_with_script(word_timings, script)
            except Exception as e:
                self.logger.warning(f"Error using Whisper library: {str(e)}, falling back to estimate")
            
            # If Whisper fails, fall back to the estimation method
            return self._generate_caption_timings(script, mpy.AudioFileClip(audio_path).duration)
        except Exception as e:
            self.logger.error(f"Error getting Whisper timestamps: {str(e)}")
            # Fall back to estimation if all else fails
            return self._generate_caption_timings(script, mpy.AudioFileClip(audio_path).duration)
    
    async def _whisper_transcribe_python(self, audio_path):
        """
        Use the Python Whisper library to transcribe audio and get word-level timestamps.
        
        Args:
            audio_path (str): Path to the audio file
            
        Returns:
            list: Word-level transcription data
        """
        try:
            # If model isn't loaded yet, load it now
            if self.whisper_model is None:
                self.logger.info("Loading Whisper model on demand...")
                self.whisper_model = whisper.load_model("tiny")
            
            # Run transcription in a thread pool to avoid blocking
            self.logger.info(f"Transcribing audio file {audio_path}")
            
            # Use run_in_executor to run CPU-intensive task in a thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,  # Use default executor
                lambda: self.whisper_model.transcribe(
                    audio_path,
                    language="en",
                    word_timestamps=True
                )
            )
            
            self.logger.info("Transcription complete")
            
            # Extract word timings from segments
            words_with_timing = []
            
            for segment in result.get('segments', []):
                for word_info in segment.get('words', []):
                    # The format might be slightly different from the CLI output
                    words_with_timing.append({
                        'word': word_info.get('word', '').strip(),
                        'start': word_info.get('start', 0),
                        'end': word_info.get('end', 0),
                        'highlighted': False  # Will be set during alignment
                    })
            
            self.logger.info(f"Extracted {len(words_with_timing)} words with timestamps")
            return words_with_timing
        except Exception as e:
            self.logger.error(f"Error in Python Whisper transcription: {str(e)}")
            raise
    
    def _align_transcription_with_script(self, whisper_words, script):
        """
        Align the Whisper transcription with the original script using fuzzy matching.
        
        Args:
            whisper_words (list): List of word dictionaries from Whisper
            script (str): The original script
            
        Returns:
            list: Caption data with aligned word timing
        """
        # Clean up the script and split into words
        script_words = re.findall(r"[\w']+|[,.!?:;\-]", script.lower())
        
        # Get just the words from whisper
        transcribed_words = [w['word'].lower() for w in whisper_words]
        
        # Keep track of matches for debugging
        self.logger.info(f"Script words: {len(script_words)}, Transcribed words: {len(whisper_words)}")
        
        # Initialize aligned words list
        aligned_words = []
        
        # For each script word, find the best matching word in the transcription
        script_idx = 0
        trans_idx = 0
        
        while script_idx < len(script_words) and trans_idx < len(whisper_words):
            script_word = script_words[script_idx]
            
            # Try to find a good match within the next few transcribed words
            best_match_idx = None
            best_match_score = 0
            
            for look_ahead in range(min(10, len(whisper_words) - trans_idx)):
                match_idx = trans_idx + look_ahead
                trans_word = transcribed_words[match_idx]
                
                # Calculate similarity score
                similarity = self._word_similarity(script_word, trans_word)
                
                if similarity > best_match_score and similarity > 0.6:  # 60% similarity threshold
                    best_match_score = similarity
                    best_match_idx = match_idx
            
            if best_match_idx is not None:
                # Use timing from the matched transcribed word
                timing = whisper_words[best_match_idx]
                aligned_words.append({
                    'word': script_word,
                    'start': timing['start'],
                    'end': timing['end'],
                    'highlighted': (script_idx % 4 == 0) and not re.match(r'^[,.!?:;\-]$', script_word)
                })
                
                # Advance indices
                script_idx += 1
                trans_idx = best_match_idx + 1
            else:
                # No good match found, estimate timing for this word
                if trans_idx < len(whisper_words):
                    # If there are still transcribed words, interpolate timing
                    timing = whisper_words[trans_idx]
                    # Estimate very short duration for this word
                    word_duration = 0.2
                    aligned_words.append({
                        'word': script_word,
                        'start': timing['start'],
                        'end': timing['start'] + word_duration,
                        'highlighted': (script_idx % 4 == 0) and not re.match(r'^[,.!?:;\-]$', script_word)
                    })
                script_idx += 1
                # Don't advance trans_idx to try matching the next script word
        
        # Package it as a single caption segment
        if aligned_words:
            # Sort by start time to ensure proper order
            aligned_words.sort(key=lambda w: w['start'])
            
            caption_data = [{
                "start": 0,
                "end": aligned_words[-1]['end'] + 1,  # End 1 second after last word
                "words": aligned_words
            }]
            return caption_data
        else:
            # If alignment failed, fall back to estimation
            audio_duration = aligned_words[-1]['end'] if aligned_words else 0
            if audio_duration == 0:
                audio_duration = whisper_words[-1]['end'] if whisper_words else 60
            return self._generate_caption_timings(script, audio_duration)
    
    def _word_similarity(self, word1, word2):
        """
        Calculate similarity between two words using sequence matcher.
        
        Args:
            word1 (str): First word
            word2 (str): Second word
            
        Returns:
            float: Similarity score between 0 and 1
        """
        if not word1 or not word2:
            return 0
        
        # Exact match
        if word1 == word2:
            return 1.0
            
        # Clean up words (remove punctuation)
        word1 = re.sub(r'[^\w\']', '', word1.lower())
        word2 = re.sub(r'[^\w\']', '', word2.lower())
        
        if not word1 or not word2:
            return 0
            
        # For very short words, require exact match
        if len(word1) <= 2 or len(word2) <= 2:
            return 1.0 if word1 == word2 else 0.0
            
        # Use sequence matcher for longer words
        return SequenceMatcher(None, word1, word2).ratio()
    
    def _crop_to_aspect(self, video, aspect=9/16, overflow=False):
        """
        Crop a video to the specified aspect ratio.
        
        Args:
            video (VideoClip): The video to crop
            aspect (float): The desired aspect ratio
            overflow (bool): Whether to allow overflow
            
        Returns:
            VideoClip: The cropped video
        """
        (w, h) = video.size
        if overflow:
            # Resize without using the problematic PIL.Image.ANTIALIAS
            # Just use the original size
            pass
            
        new_w = int(min(w, aspect * h))
        new_h = int(min(h, w / aspect))

        cropped = vfx.crop(
            video, 
            width=new_w, 
            height=new_h, 
            x_center=int(w / 2), 
            y_center=int(h / 2)
        )
        return cropped
    
    def _generate_caption_timings(self, script, duration):
        """
        Generate caption timings for the script.
        Used as fallback when Whisper transcription fails.
        
        Args:
            script (str): The script text
            duration (float): The audio duration in seconds
            
        Returns:
            list: List of caption segments with timing information
        """
        try:
            self.logger.info("Generating fallback caption timings")
            
            # For better sync, use a single segment approach instead of sentences
            # This avoids issues with sentence segmentation affecting timing
            
            # First, get all words while preserving contractions
            words = []
            word_groups = script.strip().split()
            for group in word_groups:
                # Check if this is a single word (possibly with apostrophe) or multiple words with punctuation
                if re.match(r"^[\w']+[,.!?:;\-]*$", group):
                    # It's a single word (possibly with trailing punctuation)
                    words.append(group)
                else:
                    # It might contain multiple words or special characters
                    # Split while preserving apostrophes within words
                    parts = re.findall(r"[\w']+|[^\w\s]", group)
                    words.extend(parts)
            
            if not words:
                return []
            
            # Calculate average word duration, with special handling for punctuation
            # Count special characters as shorter
            total_word_weights = 0
            for word in words:
                if re.match(r'^[,.!?:;\-]$', word):  # Single punctuation
                    total_word_weights += 0.5  # Punctuation counts as half a word
                else:
                    # Words are weighted by their length
                    word_len = len(word)
                    if word_len <= 2:  # Very short words
                        total_word_weights += 0.7
                    elif word_len <= 4:  # Short words
                        total_word_weights += 0.9
                    else:  # Normal and long words
                        total_word_weights += 1.0 + min(0.5, (word_len - 5) * 0.1)  # Add small weight for longer words
            
            # Calculate base word duration
            base_word_duration = duration / total_word_weights if total_word_weights > 0 else 0.3
            
            # Prepare the words with timing
            words_meta = []
            current_time = 0
            
            for i, word in enumerate(words):
                # Set dynamic word duration based on word characteristics
                if re.match(r'^[,.!?:;\-]$', word):  # Single punctuation
                    word_duration = base_word_duration * 0.5
                    # Give extra pause after end of sentence punctuation
                    if word in ".!?":
                        word_duration = base_word_duration * 0.8
                else:
                    # Words are timed by their length
                    word_len = len(word)
                    if word_len <= 2:  # Very short words
                        word_duration = base_word_duration * 0.7
                    elif word_len <= 4:  # Short words
                        word_duration = base_word_duration * 0.9
                    else:  # Normal and long words
                        word_duration = base_word_duration * (1.0 + min(0.5, (word_len - 5) * 0.1))
                
                # Every 4th word is highlighted (except punctuation)
                highlighted = (i % 4 == 0) and not re.match(r'^[,.!?:;\-]$', word)
                
                words_meta.append({
                    "word": word,
                    "start": current_time,
                    "end": current_time + word_duration,
                    "highlighted": highlighted
                })
                
                current_time += word_duration
            
            # Package it as a single caption segment
            caption_data = [{
                "start": 0,
                "end": duration,
                "words": words_meta
            }]
            
            return caption_data
        except Exception as e:
            self.logger.error(f"Error generating caption timings: {str(e)}")
            return []
    
    def _add_captions_to_video(self, video, caption_data, audio):
        """
        Add captions to the video using the animate_text function.
        
        Args:
            video (VideoClip): The video to add captions to
            caption_data (list): List of caption segments with timing information
            audio (AudioClip): The audio clip
            
        Returns:
            VideoClip: The video with captions added
        """
        try:
            if not caption_data:
                video.audio = audio
                return video
                
            self.logger.info("Adding captions to video")
            
            # Set up font and sizing
            font = "Arial"  # Default font, would be better to check if available
            font_size = 42  # Increased size for better readability
            
            # Get video dimensions
            screensize = video.size
            total_h = screensize[1]
            total_w = screensize[0]
            
            # Extract all words with absolute timing
            all_words = []
            for segment in caption_data:
                for word_detail in segment["words"]:
                    all_words.append({
                        "word": word_detail["word"],
                        "start": word_detail["start"],
                        "end": word_detail["end"],
                        "highlighted": word_detail["highlighted"]
                    })
            
            # Create clips for each word
            text_clips = []
            
            for word_info in all_words:
                word = word_info["word"]
                word_start = word_info["start"]
                word_end = word_info["end"]
                highlighted = word_info["highlighted"]
                
                # Skip empty words
                if not word.strip():
                    continue
                
                # Create text clip for this word (with built-in shadow effect)
                word_clip = mpy.TextClip(
                    word,
                    fontsize=font_size,
                    font=font,
                    color="red" if highlighted else "white",
                    stroke_width=2,
                    stroke_color="black",
                    method='caption'
                )
                
                # Position word at center bottom
                word_w, word_h = word_clip.size
                position_x = total_w // 2 - word_w // 2
                position_y = int(total_h * 0.85)  # Lower on screen (85% of height)
                
                # Add word clip with precise timing
                text_clips.append((word_clip
                    .set_position((position_x, position_y))
                    .set_start(word_start)
                    .set_end(word_end)))
            
            # Create final video with all clips
            # Make sure the final video has the original duration
            if text_clips:
                result = mpy.CompositeVideoClip(
                    [video] + text_clips,
                    size=video.size
                ).set_duration(video.duration)
                
                # Set audio properly
                result.audio = audio
                
                return result
            else:
                # If no text clips created, return original video with audio
                video.audio = audio
                return video
                
        except Exception as e:
            self.logger.error(f"Error adding captions to video: {str(e)}")
            # Fallback to returning the video without captions
            video.audio = audio
            return video
    
    async def cleanup(self):
        """Clean up temporary files."""
        self.logger.info("Cleaning up temporary files in video service")
        for file in self.temp_dir.glob("*"):
            try:
                file.unlink()
            except Exception as e:
                self.logger.error(f"Error cleaning up file {file}: {str(e)}")
                pass 