# Google Cloud Run Deployment Guide

This guide will help you deploy your Liroo backend to Google Cloud Run using source code deployment (not Docker).

## Prerequisites

1. **Google Cloud Account**: You need a Google Cloud account with billing enabled
2. **gcloud CLI**: Install the Google Cloud CLI
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Or download from: https://cloud.google.com/sdk/docs/install
   ```
3. **Authentication**: Login to gcloud
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

## Setup Steps

### 1. Create a Google Cloud Project

```bash
# Create a new project (or use existing)
gcloud projects create liroo-backend-$(date +%s) --name="Liroo Backend"

# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID
```

### 2. Enable Required APIs

```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable texttospeech.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

### 3. Set Up Google Cloud Storage

```bash
# Create a GCS bucket for storing images
gsutil mb gs://liroo-backend-images-$PROJECT_ID

# Make bucket publicly readable (for serving images)
gsutil iam ch allUsers:objectViewer gs://liroo-backend-images-$PROJECT_ID
```

### 4. Set Up Firebase (Optional)

If you're using Firebase for notifications:

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or use existing
3. Download the service account key JSON file
4. Store it securely (don't commit to git)

### 5. Configure Environment Variables

You'll need to set these environment variables:

- `GENAI_API_KEY`: Your Google Generative AI API key
- `GCS_BUCKET_NAME`: Your GCS bucket name (e.g., `liroo-backend-images-$PROJECT_ID`)
- `BASE_URL`: Your Cloud Run service URL (will be provided after deployment)

## Deployment

### Option 1: Using the Deployment Script

1. Edit `deploy-cloud-run.sh` and update the `PROJECT_ID`
2. Run the deployment script:
   ```bash
   ./deploy-cloud-run.sh
   ```

### Option 2: Manual Deployment

```bash
# Deploy to Cloud Run
gcloud run deploy liroo-backend \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --concurrency 80 \
    --max-instances 10 \
    --set-env-vars="GENAI_API_KEY=your-genai-api-key,GCS_BUCKET_NAME=your-gcs-bucket-name"
```

### Option 3: Using app.yaml (Alternative)

```bash
# Deploy using app.yaml configuration
gcloud run services replace app.yaml
```

## Post-Deployment Configuration

### 1. Update Environment Variables

After deployment, update your environment variables in the Google Cloud Console:

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Select your service
3. Go to "Edit & Deploy New Revision"
4. Under "Variables & Secrets", add:
   - `GENAI_API_KEY`: Your actual API key
   - `GCS_BUCKET_NAME`: Your bucket name
   - `BASE_URL`: Your service URL

### 2. Set Up Firebase Service Account (if using Firebase)

1. In Cloud Run Console, go to "Edit & Deploy New Revision"
2. Under "Variables & Secrets" → "Secrets"
3. Create a new secret with your Firebase service account JSON
4. Reference it in environment variables

### 3. Configure IAM Permissions

```bash
# Get the service account email
SERVICE_ACCOUNT=$(gcloud run services describe liroo-backend --region us-central1 --format="value(spec.template.spec.serviceAccountName)")

# Grant Storage Admin role for GCS access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/storage.admin"

# Grant AI Platform Developer role for GenAI access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/aiplatform.developer"
```

## Testing Your Deployment

### 1. Health Check

```bash
# Get your service URL
SERVICE_URL=$(gcloud run services describe liroo-backend --region us-central1 --format="value(status.url)")

# Test health endpoint
curl $SERVICE_URL/health
```

### 2. Test Comic Generation

```bash
# Test the comic generation endpoint
curl -X POST $SERVICE_URL/generate_comic \
  -H "Content-Type: application/json" \
  -d '{
    "text": "A person walking in the park on a sunny day.",
    "level": "intermediate",
    "image_style": "Comic Book"
  }'
```

### 3. Update Your Test Script

Update `test_generate_comic.py` with your new service URL:

```python
# Update these lines in test_generate_comic.py
SERVER_HOST = 'your-service-url'  # e.g., 'liroo-backend-abc123-uc.a.run.app'
SERVER_PORT = '443'  # Cloud Run uses HTTPS on port 443
```

## Monitoring and Logs

### View Logs

```bash
# View real-time logs
gcloud run services logs tail liroo-backend --region us-central1

# View recent logs
gcloud run services logs read liroo-backend --region us-central1
```

### Monitor Performance

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Select your service
3. View metrics, logs, and performance data

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are in `requirements.txt`
2. **Permission Errors**: Check IAM roles and service account permissions
3. **Timeout Errors**: Increase timeout in deployment configuration
4. **Memory Issues**: Increase memory allocation if needed

### Debug Commands

```bash
# Check service status
gcloud run services describe liroo-backend --region us-central1

# View detailed logs
gcloud run services logs read liroo-backend --region us-central1 --limit=50

# Check environment variables
gcloud run services describe liroo-backend --region us-central1 --format="value(spec.template.spec.containers[0].env[].name,spec.template.spec.containers[0].env[].value)"
```

## Cost Optimization

1. **Set min_instances to 0** for cost savings (cold starts)
2. **Use appropriate memory/CPU** allocation
3. **Monitor usage** in Google Cloud Console
4. **Set up billing alerts**

## Security Considerations

1. **Environment Variables**: Never commit API keys to git
2. **Service Account**: Use least privilege principle
3. **HTTPS**: Cloud Run automatically provides HTTPS
4. **Authentication**: Consider adding authentication if needed

## Next Steps

1. Set up a custom domain (optional)
2. Configure CI/CD pipeline
3. Set up monitoring and alerting
4. Implement caching strategies
5. Add authentication if required

## Support

If you encounter issues:

1. Check the [Cloud Run documentation](https://cloud.google.com/run/docs)
2. Review logs in Google Cloud Console
3. Check [Stack Overflow](https://stackoverflow.com/questions/tagged/google-cloud-run)
4. Contact Google Cloud support if needed 