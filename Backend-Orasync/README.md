# Liroo Backend API

A Flask-based backend service for the Liroo iOS application, providing AI-powered content generation, text-to-speech, and image generation capabilities using Google's Gemini models.

## Overview

The Liroo backend is responsible for:
- Content generation and adaptation (stories, lectures, comics, detailed explanations)
- Text-to-speech synthesis using Gemini 2.5 Flash Preview TTS
- Image generation using Gemini image models
- Content processing with reading level adaptation
- Storage management for generated assets

## Architecture

### Technology Stack
- **Framework**: Flask 3.1.0
- **AI Models**: Google Gemini (2.5 Flash, 3.0 Pro Exp)
- **Storage**: Google Cloud Storage
- **TTS**: Google Cloud Text-to-Speech API
- **Deployment**: Cloud Run (recommended) or any containerized environment

### Key Components
- Content generation pipeline with reading level adaptation
- Image generation with fallback chain (multiple model support)
- TTS generation for narration
- Async processing for long-running tasks
- Progress tracking for content generation

## Prerequisites

- Python 3.9 or higher
- Google Cloud Platform account with:
  - Gemini API enabled
  - Cloud Storage bucket created
  - Service account with appropriate permissions
- Firebase project (optional, for additional features)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Backend-Orasync
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
GENAI_API_KEY=your_gemini_api_key_here
BASE_URL=https://your-backend-url.run.app
GCS_BUCKET_NAME=your-gcs-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### 5. Set Up Google Cloud Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Create a new service account or use an existing one
3. Grant the following roles:
   - Storage Admin (for GCS bucket access)
   - AI Platform User (for Gemini API)
4. Download the JSON key file
5. Set `GOOGLE_APPLICATION_CREDENTIALS` to the path of this file

### 6. Get Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file as `GENAI_API_KEY`

## Running the Application

### Development Mode

```bash
flask --app backend:app run --debug
```

The server will start on `http://127.0.0.1:5000/`

### Production Mode (Gunicorn)

```bash
gunicorn --bind 0.0.0.0:8080 --workers 4 --timeout 300 backend:app
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 300 backend:app
```

## API Endpoints

### Health Check

```http
GET /
```

Returns server status.

### Content Processing

```http
POST /process
Content-Type: application/json

{
  "input_text": "Your text here",
  "level": "moderate",
  "summarization_tier": "detailedExplanation",
  "image_style": "ghibli"
}
```

### Story Generation

```http
POST /generate_story
Content-Type: application/json

{
  "input_text": "A brave knight and a friendly dragon",
  "level": "beginner",
  "genre": "adventure",
  "main_character": "Alex",
  "image_style": "ghibli"
}
```

### Lecture Generation

```http
POST /generate_lecture
Content-Type: application/json

{
  "input_text": "Topic to explain",
  "level": "moderate",
  "image_style": "ghibli"
}
```

### Comic Generation

```http
POST /generate_comic
Content-Type: application/json

{
  "input_text": "Story for comic",
  "level": "beginner",
  "image_style": "ghibli"
}
```

### Text-to-Speech

```http
POST /generate_tts
Content-Type: application/json

{
  "text": "Text to narrate",
  "voice": "narrator",
  "model": "gemini-2.5-flash-preview-tts"
}
```

### Image Generation

```http
POST /generate_image
Content-Type: application/json

{
  "prompt": "A vibrant coral reef",
  "level": "moderate",
  "style_hint": "ghibli"
}
```

### Progress Tracking

```http
GET /progress/{request_id}
```

Check the progress of long-running generation tasks.

## Configuration

### Reading Levels

The backend supports the following reading levels:
- `beginner` (Kid): Simple vocabulary, short sentences (ages 6-10)
- `moderate` (PreTeen): Medium complexity (ages 10-13)
- `intermediate` (Teen): Standard vocabulary (ages 13-18)
- `advanced` (University): Complex structures (ages 18+)

### Image Styles

Available image generation styles:
- `ghibli`: Studio Ghibli-inspired artwork
- `realistic`: Photorealistic images
- `cartoon`: Cartoon-style illustrations
- `watercolor`: Watercolor painting style
- `digital_art`: Digital art style

### Content Types

- `story`: Narrative stories with chapters
- `lecture`: Educational lectures with audio
- `comic`: Multi-panel comic strips
- `detailedExplanation`: Comprehensive explanations with quizzes

## Error Handling

The backend includes comprehensive error handling:
- Retry logic for API failures
- Graceful degradation with fallback models
- Detailed error messages for debugging
- Progress tracking for long operations

## Security Considerations

- Never commit `.env` files or service account keys
- Use environment variables for all sensitive data
- Implement rate limiting in production
- Use HTTPS for all API communications
- Regularly rotate API keys

## Development

### Project Structure

```
Backend-Orasync/
├── backend.py              # Main application file
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── README.md              # This file
└── lecture_output/        # Generated lecture outputs (gitignored)
```

### Adding New Features

1. Add new route handlers in `backend.py`
2. Update error handling as needed
3. Add tests for new endpoints
4. Update this README with new endpoint documentation

## Troubleshooting

### Common Issues

**Issue**: `GOOGLE_APPLICATION_CREDENTIALS not found`
- Solution: Ensure the path to your service account JSON is correct and the file exists

**Issue**: `GENAI_API_KEY is None`
- Solution: Check that your `.env` file is loaded and contains the correct key

**Issue**: GCS bucket access denied
- Solution: Verify your service account has Storage Admin role

**Issue**: Image generation fails
- Solution: Check API quotas and ensure you have sufficient credits

## License

[Add your license here]

## Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 style guidelines
- All environment variables are documented
- New endpoints include error handling
- README is updated with new features
