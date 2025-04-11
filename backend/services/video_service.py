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
                words = re.findall(r'\b\w+\b|[^\w\s]', sentence)
                if not words:
                    continue
                
                word_duration = sentence_duration / len(words)
                words_meta = []
                word_time = current_time
                
                for i, word in enumerate(words):
                    # Define if this word should be highlighted (every 3rd word)
                    highlighted = (i % 3 == 0)
                    
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
            
            # Process each caption segment
            captioned_video = video
            captioned_video.audio = audio  # Set audio to the video
            
            for segment in caption_data:
                segment_start = segment["start"]
                captioned_video = self.animate_text(
                    captioned_video,
                    segment_start,
                    [segment],  # Pass as a list of one segment
                    audio,
                    font,
                    font_size
                )
            
            return captioned_video
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
        text_color="white",
        stroke_color="black",
        stroke_width=8,
        highlight_color="red",
        fade_duration=0.3,
        stay_duration=0.8,
        wrap_width_ratio=0.8,
        shadow_offset=5,
        shadow_grow=3,
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
                    )
                    word_shadow = mpy.TextClip(
                        word,
                        fontsize=font_size,
                        font=font,
                        color=stroke_color,
                        stroke_width=stroke_width + shadow_grow,
                        stroke_color=stroke_color,
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

                curr_h = int((total_h - height) / 2)
                for line_items, line_width, line_height in all_lines:
                    curr_w = int((total_w - line_width) / 2)
                    for word_clip, word_shadow, word_start, word_end in line_items:
                        text_clips.append(
                            word_clip.set_position((curr_w, curr_h))
                            .set_start(word_start)
                            .set_end(sentence_end_t)
                            .crossfadein(fade_duration)
                            .crossfadeout(fade_duration)
                        )
                        text_shadows.append(
                            word_shadow.set_position(
                                (curr_w + shadow_offset, curr_h + shadow_offset)
                            )
                            .set_start(word_start)
                            .set_end(sentence_end_t)
                            .crossfadein(fade_duration)
                            .crossfadeout(fade_duration)
                        )
                        curr_w += word_clip.size[0]
                    curr_h += line_height

            # Create the caption overlay
            captions = mpy.CompositeVideoClip([video] + text_shadows + text_clips)
            
            # We don't need to reset the audio here as it's already set on the input video
            # and we're returning a composite that includes the original video
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