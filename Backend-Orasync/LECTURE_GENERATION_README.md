# Lecture Generation Feature

This document describes the new lecture generation functionality that has been added to the backend.

## Overview

The lecture generation feature allows you to convert academic or article text into an engaging spoken lecture with:
- **Audio narration** using Google Cloud Text-to-Speech
- **Visual illustrations** for each section
- **Structured content** broken down into digestible sections
- **Multiple reading levels** support

## Features

### 🎙️ Text-to-Speech
- Uses Google Cloud Text-to-Speech with high-quality Chirp HD3 voices
- Generates MP3 audio files for each section
- Supports natural, casual speaking style
- Audio files are stored in Google Cloud Storage with signed URLs

### 🎨 Image Generation
- Creates illustrations for each lecture section
- Supports multiple art styles (Studio Ghibli, Educational, Disney Classic, etc.)
- Images are generated using Google's Gemini image generation
- Stored in Google Cloud Storage with signed URLs

### 📚 Content Structure
- Breaks down text into 3-5 logical sections
- Each section has a catchy title, script, and image prompt
- Adapts content complexity based on reading level
- Maintains educational value while being engaging

## API Endpoint

### POST `/generate_lecture`

**Request Body:**
```json
{
  "text": "Your academic or article text here...",
  "level": "Teen",  // Optional: Kid, PreTeen, Teen, University, Standard
  "image_style": "Studio Ghibli"  // Optional: art style preference
}
```

**Response:**
```json
{
  "lecture": {
    "title": "Lecture Title",
    "sections": [
      {
        "title": "Section 1 Title",
        "script": "Section 1 content...",
        "image_prompt": "Description for image generation",
        "image_url": "https://signed-url-to-image.png"
      }
    ]
  },
  "audio_files": [
    {
      "type": "title",
      "text": "Lecture Title",
      "url": "https://signed-url-to-audio.mp3",
      "filename": "lecture_123_title.mp3"
    },
    {
      "type": "section_title",
      "text": "Section 1 Title",
      "url": "https://signed-url-to-audio.mp3",
      "filename": "lecture_123_section_1_title.mp3",
      "section": 1
    },
    {
      "type": "section_script",
      "text": "Section 1 content...",
      "url": "https://signed-url-to-audio.mp3",
      "filename": "lecture_123_section_1_script.mp3",
      "section": 1
    }
  ],
  "lecture_id": "unique-lecture-id"
}
```

## Setup Requirements

### 1. Google Cloud Credentials
You need to set up Google Cloud authentication for Text-to-Speech:

```bash
# Option 1: Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"

# Option 2: Use gcloud CLI
gcloud auth application-default login
```

### 2. Dependencies
Install the required packages:

```bash
pip install -r requirements.txt
```

The new dependencies are:
- `google-cloud-texttospeech==2.18.0`
- `google-cloud-storage==2.14.0`

### 3. Environment Variables
Make sure your `.env` file includes:
```
GENAI_API_KEY=your_gemini_api_key
GCS_BUCKET_NAME=your_google_cloud_storage_bucket
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
```

## Usage Examples

### Python Example
```python
import requests

# Generate a lecture
response = requests.post("http://localhost:5000/generate_lecture", json={
    "text": "Your academic text here...",
    "level": "Teen",
    "image_style": "Studio Ghibli"
})

if response.status_code == 200:
    result = response.json()
    lecture = result["lecture"]
    audio_files = result["audio_files"]
    
    print(f"Lecture: {lecture['title']}")
    print(f"Audio files: {len(audio_files)}")
```

### JavaScript Example
```javascript
const response = await fetch('/generate_lecture', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    text: 'Your academic text here...',
    level: 'Teen',
    image_style: 'Studio Ghibli'
  })
});

const result = await response.json();
console.log('Lecture:', result.lecture);
console.log('Audio files:', result.audio_files);
```

## Testing

Run the test script to verify the functionality:

```bash
python test_lecture.py
```

This will:
1. Check if the backend is running
2. Send a sample request to the lecture generation endpoint
3. Display the results including lecture structure and audio files

## Reading Levels

- **Kid**: Simple vocabulary, very short sentences, lots of examples (ages 6-10)
- **PreTeen**: Slightly more complex words, short to medium sentences (ages 10-13)
- **Teen**: Standard vocabulary, varied sentence length, relatable examples (ages 13-18)
- **University**: More complex vocabulary and sentence structures (ages 18+)
- **Standard**: Default level, similar to Teen

## Image Styles

- **Studio Ghibli**: Whimsical, cinematic, hand-drawn aesthetic
- **Educational**: Clear and simple, child-friendly illustrations
- **Disney Classic**: Hand-drawn, vibrant colors, magical atmosphere
- **Comic Book**: Bold lines, dynamic composition, pop art colors
- **Watercolor**: Soft edges, flowing colors, artistic
- **Pixel Art**: Retro gaming aesthetic, 8-bit inspired
- **3D Render**: Photorealistic, modern, detailed textures

## Error Handling

The endpoint includes comprehensive error handling:
- Invalid input validation
- Google Cloud service errors
- Image generation failures
- Audio generation failures
- JSON parsing errors

All errors are logged and returned with appropriate HTTP status codes.

## File Management

- Audio files are temporarily created locally, uploaded to GCS, then cleaned up
- Images are generated and stored directly in GCS
- All files use signed URLs with 60-minute expiration
- Unique filenames prevent conflicts

## Performance Considerations

- Large texts are truncated to 8000 characters for processing
- Audio generation can take time for longer scripts
- Image generation is done in parallel with audio generation
- Consider implementing caching for repeated requests 