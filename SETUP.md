# Setup Guide

This guide will walk you through setting up Liroo for development and production.

## Quick Start Checklist

- [ ] Clone the repository
- [ ] Set up Firebase project
- [ ] Configure `GoogleService-Info.plist`
- [ ] Set up backend service
- [ ] Configure environment variables
- [ ] Build and run iOS app

## Detailed Setup

### 1. Repository Setup

```bash
git clone <repository-url>
cd Liroo
```

### 2. Firebase Configuration

1. **Create Firebase Project**
   - Go to [Firebase Console](https://console.firebase.google.com)
   - Click "Add project"
   - Follow the setup wizard

2. **Enable Services**
   - Authentication → Enable Email/Password
   - Firestore Database → Create database
   - Storage → Enable Cloud Storage

3. **Get Configuration File**
   - Project Settings → General
   - Download `GoogleService-Info.plist`
   - Copy to `Liroo/Application/GoogleService-Info.plist`
   - **Important**: This file is gitignored. Never commit it.

4. **Configure Security Rules**
   - Set up Firestore security rules
   - Configure Storage rules
   - Test rules in Firebase Console

### 3. Backend Setup

1. **Navigate to Backend Directory**
   ```bash
   cd Backend-Orasync
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Set Up Google Cloud**
   - Create GCP project
   - Enable Gemini API
   - Enable Cloud Storage API
   - Create service account with Storage Admin role
   - Download service account JSON key
   - Set `GOOGLE_APPLICATION_CREDENTIALS` in `.env`

6. **Get Gemini API Key**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create API key
   - Add to `.env` as `GENAI_API_KEY`

7. **Test Backend**
   ```bash
   flask --app backend:app run
   # Should see: Running on http://127.0.0.1:5000
   ```

### 4. iOS App Configuration

1. **Open Project**
   ```bash
   open Liroo.xcodeproj
   ```

2. **Configure Backend URL**
   - Option 1: Set environment variable `BACKEND_URL`
   - Option 2: Edit `Liroo/Core/Utilities/AppConfig.swift`
   - For local development: `http://localhost:5000`
   - For production: Your deployed backend URL

3. **Verify Firebase Configuration**
   - Ensure `GoogleService-Info.plist` is in project
   - Check that Firebase packages are resolved
   - Build project to verify dependencies

4. **Build and Run**
   - Select target device
   - Build (⌘B)
   - Run (⌘R)

### 5. Production Deployment

#### Backend (Cloud Run)

1. **Build Docker Image**
   ```bash
   docker build -t liroo-backend .
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy liroo-backend \
     --image gcr.io/YOUR_PROJECT/liroo-backend \
     --platform managed \
     --region us-central1
   ```

3. **Set Environment Variables**
   ```bash
   gcloud run services update liroo-backend \
     --set-env-vars GENAI_API_KEY=your_key,GCS_BUCKET_NAME=your_bucket
   ```

#### iOS App

1. **Update Backend URL**
   - Set `BACKEND_URL` to production URL
   - Or update `AppConfig.swift`

2. **Archive and Distribute**
   - Product → Archive
   - Distribute to App Store or TestFlight

## Troubleshooting

### Common Issues

**Firebase not initializing**
- Check `GoogleService-Info.plist` is in project
- Verify bundle ID matches Firebase project
- Ensure Firebase packages are installed

**Backend connection failed**
- Verify backend is running
- Check `BACKEND_URL` is correct
- Test backend health endpoint: `GET /health`

**API key errors**
- Verify `.env` file exists and is loaded
- Check API key is valid and has proper permissions
- Ensure service account has correct roles

**Image generation fails**
- Check GCS bucket exists and is accessible
- Verify service account has Storage Admin role
- Check API quotas and billing

## Security Checklist

Before deploying to production:

- [ ] Remove all hardcoded credentials
- [ ] Use environment variables for all secrets
- [ ] Verify `.gitignore` excludes sensitive files
- [ ] Review Firebase security rules
- [ ] Enable API key restrictions
- [ ] Set up proper CORS configuration
- [ ] Use HTTPS for all API calls
- [ ] Implement rate limiting
- [ ] Set up monitoring and logging

## Next Steps

- Review [README.md](README.md) for feature documentation
- Check [Backend README](Backend-Orasync/README.md) for API details
- Explore the codebase structure
- Set up CI/CD pipeline
- Configure monitoring and analytics

