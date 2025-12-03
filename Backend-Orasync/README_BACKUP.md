# Liroo Backup Backend

This is a backup version of the Liroo backend with improved stability and error handling.

## Features

- **Enhanced Image Processing**: Better handling of GenAI image responses
- **Rate Limit Management**: Exponential backoff and retry logic
- **Memory Management**: Aggressive garbage collection and memory monitoring
- **Error Recovery**: Robust fallback mechanisms for failed image generation
- **Progress Tracking**: Real-time progress updates for long-running operations
- **Health Checks**: Dedicated health check endpoints

## Setup

### 1. Environment Configuration

Run the setup script to configure environment variables:

```bash
./setup_env.sh
```

This will prompt you for:
- **GenAI API Key**: Your Google GenAI API key
- **GCS Bucket Name**: Your Google Cloud Storage bucket name
- **Port**: Port number for the backend (default: 5001)

### 2. Google Cloud Authentication

Make sure you're authenticated with Google Cloud:

```bash
gcloud auth application-default login
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Running the Backup Backend

### Start the Server

```bash
python backend_backup.py
```

The backend will start on the configured port (default: 5001).

### Health Check

Check if the backend is running:

```bash
curl http://localhost:5001/backup-health
```

## API Endpoints

### Health Check
- **GET** `/backup-health` - Backup-specific health check
- **GET** `/health` - General health check

### Content Generation
- **POST** `/process` - Generate educational content
- **POST** `/generate_story` - Generate stories with images
- **POST** `/generate_comic` - Generate comics with panel images
- **POST** `/generate_lecture` - Generate lectures with audio and images

### Progress Tracking
- **GET** `/progress/<request_id>` - Get progress for a specific request

## Troubleshooting

### Rate Limiting Issues

If you encounter rate limiting errors:

1. **Check your GenAI quota**: Visit [Google AI Studio](https://aistudio.google.com/) to check your usage
2. **Wait and retry**: The backend includes exponential backoff for rate limits
3. **Reduce concurrent requests**: The backend processes images sequentially to avoid overwhelming the API

### Image Generation Failures

If images fail to generate:

1. **Check GCS bucket**: Ensure your bucket exists and is accessible
2. **Verify authentication**: Run `gcloud auth application-default login`
3. **Check environment variables**: Ensure `GCS_BUCKET_NAME` is set correctly

### Memory Issues

If you encounter memory problems:

1. **Reduce panel count**: The backend limits comics to 10 panels maximum
2. **Monitor memory usage**: The backend includes memory monitoring (requires `psutil`)
3. **Restart the server**: If memory usage gets too high

## Configuration

### Environment Variables

- `GENAI_API_KEY`: Your Google GenAI API key
- `GCS_BUCKET_NAME`: Your Google Cloud Storage bucket name
- `PORT`: Port number for the backend (default: 5001)
- `BACKUP_MODE`: Set to `true` for backup mode
- `BACKUP_DEBUG`: Set to `true` for debug logging

### Rate Limiting

The backend includes several rate limiting features:

- **Exponential backoff**: 20s, 40s, 60s delays between retries
- **Sequential processing**: Images are generated one at a time
- **Memory cleanup**: Aggressive garbage collection between operations

## Differences from Main Backend

1. **Better Error Handling**: More robust error recovery
2. **Rate Limit Management**: Improved handling of API quotas
3. **Memory Management**: Better memory usage and cleanup
4. **Progress Tracking**: Enhanced progress reporting
5. **Fallback Mechanisms**: Better fallbacks when operations fail

## Support

If you encounter issues:

1. Check the logs for detailed error messages
2. Verify your environment variables are set correctly
3. Ensure you have sufficient GenAI quota
4. Check that your GCS bucket is accessible 