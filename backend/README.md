# Brainrotify Backend

This is the backend service for the Brainrotify application, which generates "brain rot" content videos using AI.

## Features

- Script generation using Venice AI
- Text-to-speech conversion
- Image generation
- Video creation with animated text using MoviePy
- IPFS upload for videos and metadata

## Setup

1. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your Venice AI API key:

   ```
   VENICE_KEY=your_venice_api_key
   ```

3. Install system dependencies (required for MoviePy):
   - On macOS: `brew install ffmpeg imagemagick`

## Running the Server

```
python -m uvicorn main:app --reload
```

The API will be available at <http://localhost:8000>

## API Endpoints

### GET /

Returns a welcome message to verify the API is running.

### POST /generate

Generates a brain rot video based on the provided content and style.

**Request Body:**

```json
{
  "content": "Chernobyl",
  "style": "Minecraft Parkour",
  "duration": 60
}
```

**Response:**

```json
{
  "metadata_uri": "ipfs://Qm...",
  "video_uri": "ipfs://Qm...",
  "script": "..."
}
```

## Docker

You can also run the backend using Docker:

```
docker build -t brainrotify-backend .
docker run -p 8000:8000 --env-file .env brainrotify-backend
```
