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

class VideoService:
    def __init__(self):
        # Create a temp directory for processing
        self.temp_dir = Path(tempfile.gettempdir()) / "brainrotify_video"
        os.makedirs(self.temp_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
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
            
            # Generate caption timings based on the script
            caption_data = self._generate_caption_timings(script, duration)
            self.logger.info(f"Generated {len(caption_data)} caption segments")
            self.logger.info(caption_data)
            
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
        Since we don't have access to true word-level timing from the TTS engine,
        we'll estimate timings based on text length and total duration.
        
        Args:
            script (str): The script text
            duration (float): The audio duration in seconds
            
        Returns:
            list: List of caption segments with timing information
        """
        try:
            self.logger.info("Generating caption timings")
            
            # Split the script into sentences
            sentences = re.split(r'(?<=[.!?])\s+', script.strip())
            sentences = [s for s in sentences if s.strip()]
            
            if not sentences:
                return []
            
            # Estimate the duration for each sentence based on character count
            total_chars = sum(len(s) for s in sentences)
            char_duration = duration / total_chars if total_chars > 0 else 0
            
            caption_data = []
            current_time = 0
            
            for sentence in sentences:
                # Estimate sentence duration based on character count
                sentence_chars = len(sentence)
                sentence_duration = sentence_chars * char_duration
                
                # Create word-level timing within the sentence
                # Use a regex that keeps contractions and words with apostrophes together
                words = []
                # First split by spaces to get word groups
                word_groups = sentence.split()
                for group in word_groups:
                    # Check if this is a single word (possibly with apostrophe) or multiple words with punctuation
                    if re.match(r"^[\w']+[,.!?:;]*$", group):
                        # It's a single word (possibly with trailing punctuation)
                        words.append(group)
                    else:
                        # It might contain multiple words or special characters
                        # Split while preserving apostrophes within words
                        parts = re.findall(r"[\w']+|[^\w\s]", group)
                        words.extend(parts)
                
                if not words:
                    continue
                
                word_duration = sentence_duration / len(words)
                words_meta = []
                word_time = current_time
                
                for i, word in enumerate(words):
                    # Define if this word should be highlighted (every 4th word)
                    highlighted = (i % 4 == 0)
                    
                    # Give end-of-sentence punctuation extra time
                    if word == '.' or word == "?" or word == "!": 
                        words_meta.append({
                            "word": word,
                            "start": word_time - current_time,  # Relative to sentence start
                            "end": word_time - current_time + 0.5,
                            "highlighted": highlighted
                        })
                        word_time += 0.5
                    else:
                        words_meta.append({
                            "word": word,
                            "start": word_time - current_time,  # Relative to sentence start
                            "end": word_time - current_time + word_duration,
                            "highlighted": highlighted
                        })
                        word_time += word_duration
                
                caption_data.append({
                    "start": current_time,
                    "end": current_time + sentence_duration,
                    "words": words_meta
                })
                
                current_time += sentence_duration
            
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
            font_size = 36
            
            # Instead of processing segments one by one, create one composite with all words
            text_clips = []
            text_shadows = []
            
            # Get video dimensions
            screensize = video.size
            total_h = screensize[1]
            total_w = screensize[0]
            
            # Flatten all words from all segments into a single chronological list
            all_words = []
            for segment in caption_data:
                segment_start = segment["start"]
                for word_detail in segment["words"]:
                    word = word_detail["word"]
                    word_start = segment_start + word_detail["start"]
                    all_words.append({
                        "word": word,
                        "start": word_start,
                        "highlighted": word_detail["highlighted"]
                    })
            
            # Sort words by their start time
            all_words.sort(key=lambda w: w["start"])
            
            # Process words chronologically, setting each word to end when the next one starts
            for i, word_info in enumerate(all_words):
                word = word_info["word"]
                word_start = word_info["start"]
                highlighted = word_info["highlighted"]
                
                # The word ends when the next word starts, or after a fixed duration for the last word
                if i < len(all_words) - 1:
                    word_end = all_words[i + 1]["start"]
                else:
                    word_end = word_start + 1.0  # Last word stays for 1 second
                
                # Create text clip for this word
                word_clip = mpy.TextClip(
                    word,
                    fontsize=font_size,
                    font=font,
                    color="red" if highlighted else "white",  # Highlighted words are red
                    stroke_width=2,
                    stroke_color="black",
                    method='caption'
                )
                
                # Create shadow for this word
                word_shadow = mpy.TextClip(
                    word,
                    fontsize=font_size,
                    font=font,
                    color="black",  # Shadow is always black
                    stroke_width=4,
                    stroke_color="black",
                    method='caption'
                )
                
                # Position word at center bottom
                word_w, word_h = word_clip.size
                position_x = total_w // 2 - word_w // 2
                position_y = int(total_h * 0.8)  # At 80% of the height
                
                # Add word clip with precise timing
                text_clips.append(
                    word_clip
                    .set_position((position_x, position_y))
                    .set_start(word_start)
                    .set_end(word_end)
                    .crossfadein(0.05)  # Quick fade in
                    .crossfadeout(0.05)  # Quick fade out
                )
                
                # Add shadow with slight offset
                text_shadows.append(
                    word_shadow
                    .set_position((position_x + 2, position_y + 2))
                    .set_start(word_start)
                    .set_end(word_end)
                    .crossfadein(0.05)
                    .crossfadeout(0.05)
                )
            
            # Create final video with all clips
            # Make sure the final video has the original duration by explicitly setting it
            result = mpy.CompositeVideoClip(
                [video] + text_shadows + text_clips,
                size=video.size
            ).set_duration(video.duration)
            
            # Set audio properly
            result.audio = audio
            
            return result
        except Exception as e:
            self.logger.error(f"Error adding captions to video: {str(e)}")
            # Fallback to returning the video without captions
            video.audio = audio
            return video
    
    def animate_text(
        self,
        video,
        time,
        text_meta,
        audioclip,
        font="Arial",
        font_size=36,
        text_color="white",  # Changed default color to white
        stroke_color="black",
        stroke_width=2,  # Reduced stroke width
        highlight_color="red",  # Changed highlight to white too
        fade_duration=0.1,  # Faster fade for better sync
        stay_duration=0.5,
        wrap_width_ratio=0.8,
        shadow_offset=2,  # Reduced shadow offset
        shadow_grow=1,  # Reduced shadow grow
    ):
        """
        Adds audio and text to a video clip

        Args:
            video (VideoClip): The video to overlay the text captions onto
            time (float): The time which the text captions should start on the video
            text_meta (list): Metadata of the captions and the time which each word appears
            audioclip (AudioClip): The audioclip to add to the video, associated with the captions
            font (str): Font to use for the text
            font_size (int): Font size
            text_color (str): Color of the text
            stroke_color (str): Color of the text stroke
            stroke_width (float): Width of the text stroke
            highlight_color (str): Color for highlighted words
            fade_duration (float): Duration of the fade effect
            stay_duration (float): How long text stays after being spoken
            wrap_width_ratio (float): Ratio of screen width to use for text wrapping
            shadow_offset (float): Offset for text shadow
            shadow_grow (float): How much to grow the shadow
            
        Returns:
            VideoClip: The composited video clip with the audio and captions added
        """
        try:
            screensize = video.size

            total_h = screensize[1]
            total_w = screensize[0]
            wrap_w = int(total_w * wrap_width_ratio)

            text_clips = []
            text_shadows = []
            for text_detail in text_meta:
                words_meta = text_detail["words"]
                sentence_start_t = text_detail["start"] + time
                sentence_end_t = text_detail["end"] + time + stay_duration

                all_word_clips = []
                for word_detail in words_meta:
                    word = word_detail["word"]
                    start_t = word_detail["start"] + sentence_start_t
                    end_t = word_detail["end"] + sentence_start_t
                    highlight = word_detail["highlighted"]
                    word_clip = mpy.TextClip(
                        word,
                        fontsize=font_size,
                        font=font,
                        color=highlight_color if highlight else text_color,
                        stroke_width=stroke_width,
                        stroke_color=stroke_color,
                        method='caption',  # Use caption method for better text rendering
                    )
                    word_shadow = mpy.TextClip(
                        word,
                        fontsize=font_size,
                        font=font,
                        color=stroke_color,
                        stroke_width=stroke_width + shadow_grow,
                        stroke_color=stroke_color,
                        method='caption',
                    )
                    all_word_clips.append((word_clip, word_shadow, start_t, end_t))

                all_lines = []
                line = []
                width = 0
                height = 0
                max_h = 0
                for word_clip, word_shadow, word_start, word_end in all_word_clips:
                    w, h = word_clip.size
                    if h > max_h:
                        max_h = h

                    if width + w > wrap_w:
                        all_lines.append(([l for l in line], width, max_h))
                        line = []
                        width = 0
                        height += max_h
                        max_h = 0

                    width += w
                    line.append((word_clip, word_shadow, word_start, word_end))
                if len(line) > 0:
                    all_lines.append(([l for l in line], width, max_h))

                curr_h = int(total_h * 0.8)  # Position text at 80% of screen height
                for line_items, line_width, line_height in all_lines:
                    curr_w = int((total_w - line_width) / 2)
                    for word_clip, word_shadow, word_start, word_end in line_items:
                        text_clips.append(
                            word_clip.set_position((curr_w, curr_h))
                            .set_start(word_start)
                            .set_end(sentence_end_t)
                            .crossfadein(fade_duration)
                        )
                        text_shadows.append(
                            word_shadow.set_position(
                                (curr_w + shadow_offset, curr_h + shadow_offset)
                            )
                            .set_start(word_start)
                            .set_end(sentence_end_t)
                            .crossfadein(fade_duration)
                        )
                        curr_w += word_clip.size[0]
                    curr_h += line_height

            # Create the caption overlay with explicit duration from the input video
            captions = mpy.CompositeVideoClip(
                [video] + text_shadows + text_clips,
                size=video.size
            ).set_duration(video.duration)
            
            return captions
        except Exception as e:
            self.logger.error(f"Error in animate_text: {str(e)}")
            return video  # Return original video on error
    
    async def cleanup(self):
        """Clean up temporary files."""
        self.logger.info("Cleaning up temporary files in video service")
        for file in self.temp_dir.glob("*"):
            try:
                file.unlink()
            except Exception as e:
                self.logger.error(f"Error cleaning up file {file}: {str(e)}")
                pass 