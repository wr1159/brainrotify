from .venice_service import VeniceService
from .video_service import VideoService
from .ipfs_service import IPFSService
import uuid
import logging

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
    
    async def generate_content(self, content, style, duration=60):
        """Generate a full video including script, TTS, image, and upload to IPFS.
        
        Args:
            content (str): The topic for the video
            style (str): The style of brainrot content
            duration (int, optional): Target duration in seconds. Defaults to 60.
            
        Returns:
            dict: Result containing metadata_uri, video_uri, and script
        """
        try:
            # 1. Generate script
            self.logger.info("Generating Script")
            script = await self.venice_service.generate_script(content, style, duration)
            
            # 2. Generate TTS audio and get the file path directly
            self.logger.info("Generating TTS")
            audio_file = await self.venice_service.generate_tts(script)
            
            # 3. Generate image and get the file path directly
            self.logger.info("Generating Image")
            image_file = await self.venice_service.generate_image(content, style)
            
            # 4. Create video with animated text
            self.logger.info("Creating Video")
            video_file = await self.video_service.create_video(image_file, audio_file, script)
            
            # 5. Upload video to IPFS
            self.logger.info("Uploading Video")
            video_uri = await self.ipfs_service.upload_file(video_file)
            
            # 6. Create metadata
            self.logger.info("Creating Metadata")
            metadata = self.ipfs_service.create_metadata(content, style, video_uri)
            
            # 7. Upload metadata to IPFS
            self.logger.info("Uploading Metadata")
            metadata_uri = await self.ipfs_service.upload_json(metadata)
            
            # 8. Cleanup temporary files
            # await self.video_service.cleanup()
            self.venice_service.cleanup()
            
            # 9. Return result
            return {
                "metadata_uri": metadata_uri,
                "video_uri": video_uri,
                "script": script
            }
        
        except Exception as e:
            # Make sure to clean up on error
            # await self.video_service.cleanup()
            self.venice_service.cleanup()
            self.logger.error(f"Error in generate_content: {str(e)}")
            raise e 