from .venice_service import VeniceService
from .video_service import VideoService
from .ipfs_service import IPFSService
import uuid
import logging
import os

class GenerationService:
    def __init__(self):
        self.venice_service = VeniceService()
        self.video_service = VideoService()
        self.ipfs_service = IPFSService()

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)
    
    async def generate_content(self, content, style, duration=60, image_count=None, ticker=None, description=None):
        """Generate a full video including script, TTS, multiple images, and upload to IPFS.
        
        Args:
            content (str): The topic for the video
            style (str): The style of brainrot content
            duration (int, optional): Target duration in seconds. Defaults to 60.
            image_count (int, optional): Number of images to generate. If None, will calculate
                                         based on audio duration (1 image per 10 seconds).
            ticker (str, optional): Ticker symbol for the NFT
            description (str, optional): Description of the video
            
        Returns:
            dict: Result containing metadata_uri, video_uri, script, and thumbnail_uri
        """
        try:
            # 1. Generate script
            self.logger.info("Generating Script")
            script = await self.venice_service.generate_script(content, style, duration)
            
            # 2. Generate TTS audio and get the file path directly
            self.logger.info("Generating TTS")
            audio_file, audio_duration = await self.venice_service.generate_tts(script)
            
            # Calculate number of images based on audio duration if not specified
            # Use 1 image per 10 seconds of audio, minimum 1 image
            if image_count is None:
                image_count = max(1, int(audio_duration / 10) + 1)
                self.logger.info(f"Calculated {image_count} images needed for {audio_duration:.2f} seconds of audio")
            
            # 3. Generate multiple images based on the script and get the file paths
            self.logger.info(f"Generating {image_count} Images")
            image_files = await self.venice_service.generate_multiple_images(content, style, script, count=image_count)
            
            # 4. Create video with multiple images and audio
            self.logger.info("Creating Video with Multiple Images")
            video_file = await self.video_service.create_video(image_files, audio_file, script)
            
            # 5. Upload first image as thumbnail
            self.logger.info("Uploading Thumbnail Image")
            thumbnail_uri = None
            if image_files and len(image_files) > 0:
                # Use the first image as the thumbnail
                thumbnail_file = image_files[0]
                # Add metadata for the thumbnail
                thumbnail_metadata = {
                    "type": "thumbnail",
                    "content": content,
                    "style": style
                }
                thumbnail_uri = await self.ipfs_service.upload_file(
                    thumbnail_file,
                    name=f"thumbnail_{content}_{style}.png",
                    keyvalues=thumbnail_metadata
                )
                self.logger.info(f"Thumbnail uploaded: {thumbnail_uri}")
            
            # 6. Upload video to IPFS
            self.logger.info("Uploading Video")
            video_uri = await self.ipfs_service.upload_file(video_file)
            
            # 7. Create metadata with thumbnail, ticker, and description
            self.logger.info("Creating Metadata")
            metadata = self.ipfs_service.create_metadata(
                content, 
                style, 
                video_uri, 
                thumbnail_uri,
                ticker,
                description
            )
            
            # 8. Upload metadata to IPFS
            self.logger.info("Uploading Metadata")
            metadata_uri = await self.ipfs_service.upload_json(metadata)
            
            # 9. Cleanup temporary files
            # await self.video_service.cleanup()
            self.venice_service.cleanup()
            
            # 10. Return result
            return {
                "metadata_uri": metadata_uri,
                "video_uri": video_uri,
                "script": script,
                "thumbnail_uri": thumbnail_uri
            }
        
        except Exception as e:
            # Make sure to clean up on error
            # await self.video_service.cleanup()
            self.venice_service.cleanup()
            self.logger.error(f"Error in generate_content: {str(e)}")
            raise e 