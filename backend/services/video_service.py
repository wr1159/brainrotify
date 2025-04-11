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
            script (str): The script text (not used directly in this implementation)
            
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
            
            # Add the audio to the video
            video.audio = audio
            
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
    
    async def cleanup(self):
        """Clean up temporary files."""
        self.logger.info("Cleaning up temporary files in video service")
        for file in self.temp_dir.glob("*"):
            try:
                file.unlink()
            except Exception as e:
                self.logger.error(f"Error cleaning up file {file}: {str(e)}")
                pass 