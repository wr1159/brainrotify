from pydantic import BaseModel, Field
from typing import Optional, List


class GenerateRequest(BaseModel):
    """Request model for the generate endpoint."""
    content: str = Field(..., description="The topic for the video (e.g., 'Chernobyl', 'Turtles')")
    style: str = Field(..., description="The style of brainrot content (e.g., 'Minecraft Parkour', 'Soap Cutting')")
    duration: Optional[int] = Field(60, description="Target duration of the video in seconds")


class GenerateResponse(BaseModel):
    """Response model for the generate endpoint."""
    metadata_uri: str = Field(..., description="IPFS URI for the metadata JSON")
    video_uri: str = Field(..., description="IPFS URI for the video file")
    script: str = Field(..., description="The generated script used for the video")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details") 