import httpx
import logging
import base64
import os
import uuid
from pathlib import Path
import tempfile
from utils.config import VENICE_API_KEY

class VeniceService:
    def __init__(self):
        self.api_key = VENICE_API_KEY
        self.base_url = "https://api.venice.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.logger = logging.getLogger(__name__)
        # Create a temp directory for processing
        self.temp_dir = Path(tempfile.gettempdir()) / "brainrotify"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    async def generate_script(self, content, style, duration_seconds=60):
        """Generate a script based on the given content and style.
        
        Args:
            content (str): The topic for the video
            style (str): The style of brainrot content (e.g., "Minecraft Parkour", "Soap Cutting")
            duration_seconds (int): Target duration of the script in seconds
            
        Returns:
            str: The generated script
        """
        try:
            self.logger.info(f"Generating script for content: {content}, style: {style}")
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": "llama-3.1-405b",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert in creating viral social media scripts in Text directly. There is only one character and that is the narrator so the script is what the narrator will narrate. Return the script directly WITHOUT any sound effects or pauses in paranthesis. Do not explain the script."
                            },
                            {
                                "role": "user",
                                "content": f"Create a viral social media script about {content} in the style of {style} brainrot videos. The script should be about {duration_seconds} seconds when read aloud."
                            }
                        ],
                        "max_tokens": 1000
                    }
                )
                response.raise_for_status()
                
                # Extract the generated text from the chat API response
                choices = response.json().get("choices", [])
                if choices and len(choices) > 0:
                    message = choices[0].get("message", {})
                    return message.get("content", "")
                return ""
        except httpx.ConnectError as e:
            self.logger.error(f"Connection error to Venice API: {str(e)}")
            raise Exception(f"Failed to connect to Venice API: {str(e)}")
        except httpx.TimeoutException as e:
            self.logger.error(f"Timeout connecting to Venice API: {str(e)}")
            raise Exception(f"Timeout connecting to Venice API: {str(e)}")
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error from Venice API: {str(e)}")
            raise Exception(f"HTTP error from Venice API: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error generating script: {str(e)}")
            raise Exception(f"Unexpected error generating script: {str(e)}")
    
    async def generate_tts(self, script):
        """Generate text-to-speech audio from the script and save to a file.
        
        Args:
            script (str): The script to convert to speech
            
        Returns:
            tuple: (Path to the saved audio file, duration in seconds)
        """
        try:
            self.logger.info("Generating TTS from script")
            self.logger.info(f"Script: {script}")
            audio_file = self.temp_dir / f"{uuid.uuid4()}.mp3"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/audio/speech",
                    headers=self.headers,
                    json={
                        "model": "tts-kokoro",
                        "input": script,
                        "voice": "am_adam"  # Using a default voice
                    }
                )
                response.raise_for_status()
                
                # Save audio data directly to file
                with open(audio_file, "wb") as f:
                    f.write(response.content)
                
                self.logger.info(f"Audio saved to {audio_file}")
                
                # Get duration of the audio file using moviepy
                try:
                    import moviepy.editor as mpy
                    audio_clip = mpy.AudioFileClip(str(audio_file))
                    duration = audio_clip.duration
                    audio_clip.close()
                    self.logger.info(f"Audio duration: {duration} seconds")
                except Exception as e:
                    self.logger.error(f"Error getting audio duration: {str(e)}")
                    # Estimate duration based on script length (about 15 characters per second as fallback)
                    duration = len(script) / 15.0
                    self.logger.info(f"Estimated audio duration: {duration} seconds (based on text length)")
                
                return str(audio_file), duration
        except httpx.ConnectError as e:
            self.logger.error(f"Connection error to Venice API: {str(e)}")
            raise Exception(f"Failed to connect to Venice API: {str(e)}")
        except httpx.TimeoutException as e:
            self.logger.error(f"Timeout connecting to Venice API: {str(e)}")
            raise Exception(f"Timeout connecting to Venice API: {str(e)}")
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error from Venice API: {str(e)}")
            raise Exception(f"HTTP error from Venice API: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error generating TTS: {str(e)}")
            raise Exception(f"Unexpected error generating TTS: {str(e)}")
    
    async def generate_image(self, content, style):
        """Generate an image for the video based on content and style, and save to a file.
        
        Args:
            content (str): The topic for the video
            style (str): The style of brainrot content
            
        Returns:
            str: Path to the saved image file
        """
        try:
            self.logger.info(f"Generating image for content: {content}, style: {style}")
            image_file = self.temp_dir / f"{uuid.uuid4()}.png"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/image/generate",
                    headers=self.headers,
                    json={
                        "model": "fluently-xl",
                        "prompt": f"Create a captivating image about {content} for tiktok videos. It should look as AI Generated as possible.",
                        "height": 512,
                        "width": 512,
                        "steps": 20,
                        "return_binary": False,
                        "hide_watermark": True,
                        "format": "png",
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if "images" not in data or not data["images"]:
                    raise Exception("No image data in response")
                
                # Decode and save image data
                image_data = base64.b64decode(data["images"][0])
                with open(image_file, "wb") as f:
                    f.write(image_data)
                
                self.logger.info(f"Image saved to {image_file}")
                return str(image_file)
        except httpx.ConnectError as e:
            self.logger.error(f"Connection error to Venice API: {str(e)}")
            raise Exception(f"Failed to connect to Venice API: {str(e)}")
        except httpx.TimeoutException as e:
            self.logger.error(f"Timeout connecting to Venice API: {str(e)}")
            raise Exception(f"Timeout connecting to Venice API: {str(e)}")
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error from Venice API: {str(e)}")
            raise Exception(f"HTTP error from Venice API: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error generating image: {str(e)}")
            raise Exception(f"Unexpected error generating image: {str(e)}")
    
    async def generate_multiple_images(self, content, style, script, count=5):
        """Generate multiple images for the video based on content, style and script.
        
        Args:
            content (str): The topic for the video
            style (str): The style of brainrot content
            script (str): The script text to use for generating varied prompts
            count (int): Number of images to generate
            
        Returns:
            list: List of paths to the saved image files
        """
        try:
            self.logger.info(f"Generating {count} images for content: {content}, style: {style}")
            image_files = []
            
            # First, use the LLM to generate different prompts based on the script
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": "llama-3.1-405b",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert at creating diverse image prompts for a video. Generate varied and interesting prompts based on the script."
                            },
                            {
                                "role": "user",
                                "content": f"Create {count} different image prompts to visualize this script about {content} in {style} style. Script: {script}. Return ONLY a numbered list of prompts."
                            }
                        ],
                        "max_tokens": 500
                    }
                )
                response.raise_for_status()
                
                # Extract the generated prompts
                choices = response.json().get("choices", [])
                if choices and len(choices) > 0:
                    prompts_text = choices[0].get("message", {}).get("content", "")
                    # Parse the numbered list
                    prompts = []
                    for line in prompts_text.strip().split("\n"):
                        if line.strip() and any(line.strip().startswith(str(i) + ".") for i in range(1, count+1)):
                            prompts.append(line.strip().split(".", 1)[1].strip())
                    
                    # If we couldn't parse enough prompts, generate some backup ones
                    while len(prompts) < count:
                        prompts.append(f"Create a captivating image about {content} for {style} style videos, image #{len(prompts)+1}")
                
                # Generate images for each prompt
                for i, prompt in enumerate(prompts[:count]):
                    image_file = self.temp_dir / f"{uuid.uuid4()}.png"
                    
                    response = await client.post(
                        f"{self.base_url}/image/generate",
                        headers=self.headers,
                        json={
                            "model": "fluently-xl",
                            "prompt": prompt,
                            "height": 512,
                            "width": 512,
                            "steps": 20,
                            "return_binary": False,
                            "hide_watermark": True,
                            "format": "png",
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    if "images" not in data or not data["images"]:
                        continue
                    
                    # Decode and save image data
                    image_data = base64.b64decode(data["images"][0])
                    with open(image_file, "wb") as f:
                        f.write(image_data)
                    
                    self.logger.info(f"Image {i+1}/{count} saved to {image_file}")
                    image_files.append(str(image_file))
                
                # If we couldn't generate enough images, repeat the original method
                if len(image_files) < count:
                    self.logger.warning(f"Could only generate {len(image_files)} images with prompts, using fallback method for remaining images")
                    remaining = count - len(image_files)
                    for i in range(remaining):
                        img_path = await self.generate_image(content, style)
                        image_files.append(img_path)
                
                return image_files
        except Exception as e:
            self.logger.error(f"Error generating multiple images: {str(e)}")
            # Fallback to single image generation if there's an error
            self.logger.info("Falling back to single image generation")
            img_path = await self.generate_image(content, style)
            return [img_path]  # Return as a list with a single item
            
    def cleanup(self):
        """Clean up temporary files created by this service."""
        for file in self.temp_dir.glob("*"):
            try:
                file.unlink()
            except Exception as e:
                self.logger.error(f"Error cleaning up file {file}: {str(e)}")
                pass 