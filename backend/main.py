from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging, time

from services import GenerationService
from models import GenerateRequest, GenerateResponse, ErrorResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Brainrotify API",
    description="API for generating brainrot content videos",
    version="0.1.0",
)

# Add CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, you would restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get the generation service
def get_generation_service():
    return GenerationService()


@app.get("/")
async def root():
    return {"message": "Welcome to Brainrotify API!"}


@app.get('/ping')
async def ping():
    return {"status": "ok", "time": time.time()}

@app.post(
    "/generate", 
    response_model=GenerateResponse,
    responses={
        200: {"model": GenerateResponse},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def generate(
    request: GenerateRequest, 
    generation_service: GenerationService = Depends(get_generation_service)
):
    """
    Generate a brainrot video based on the given content and style.
    
    This endpoint will:
    1. Generate a script using Venice AI
    2. Convert the script to speech using TTS
    3. Generate multiple images based on the content and style (1 per 10s of audio)
    4. Combine the images, speech, and subtitles into a video
    5. Upload the video to IPFS
    6. Create and upload metadata to IPFS
    7. Return the metadata URI
    
    The frontend can then use this metadata URI to mint an NFT.
    """
    try:
        logger.info(f"Generating content for topic: {request.content}, style: {request.style}")
        
        result = await generation_service.generate_content(
            request.content, 
            request.style, 
            request.duration
        )
        
        logger.info(f"Successfully generated content. Metadata URI: {result['metadata_uri']}")
        
        return GenerateResponse(
            metadata_uri=result["metadata_uri"],
            video_uri=result["video_uri"],
            script=result["script"]
        )
    
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to generate content", "details": str(e)}
        )
