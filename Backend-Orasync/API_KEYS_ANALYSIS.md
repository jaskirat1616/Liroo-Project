# 🔑 Complete API Keys & Credentials Analysis for Liroo Backend

## 📋 **Summary of Required Credentials**

Based on deep analysis of the backend code, here are **ALL** the API keys, environment variables, and credentials you need:

---

## 🚨 **CRITICAL (Required for Basic Functionality)**

### 1. **Google Generative AI API Key** ⭐⭐⭐
- **Environment Variable**: `GENAI_API_KEY`
- **Get it from**: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Usage**: 
  - Text generation (`gemini-2.5-flash-preview-04-17`)
  - Image generation (`gemini-2.0-flash-preview-image-generation`)
  - Comic generation (`gemini-2.5-pro`)
- **Cost**: Pay-per-use (first 15 requests/minute free)
- **Status**: **MANDATORY** - App won't work without this

### 2. **Google Cloud Storage Bucket** ⭐⭐⭐
- **Environment Variable**: `GCS_BUCKET_NAME`
- **Value**: `liroo-backend-images-liroo-1758a` (auto-created)
- **Usage**: Store generated images, audio files, and assets
- **Access**: Uses signed URLs (no public access needed)
- **Status**: **MANDATORY** - File storage won't work without this

### 3. **Google Cloud Project** ⭐⭐⭐
- **Current Project**: `liroo-1758a`
- **Usage**: Host the application and manage resources
- **Billing**: Must be enabled
- **Status**: **MANDATORY** - Already set up

---

## 🔧 **IMPORTANT (Required for Full Functionality)**

### 4. **Base URL** ⭐⭐
- **Environment Variable**: `BASE_URL`
- **Value**: Your Cloud Run service URL (e.g., `https://liroo-backend-abc123-uc.a.run.app`)
- **Usage**: Generate correct URLs for frontend integration
- **Status**: **REQUIRED** - Will be provided after deployment

### 5. **Google Cloud Service Account** ⭐⭐
- **Type**: Default service account (auto-configured)
- **Required IAM Roles**:
  - `roles/storage.admin` (for GCS access)
  - `roles/aiplatform.developer` (for GenAI access)
  - `roles/texttospeech.user` (for TTS access)
- **Status**: **AUTO-CONFIGURED** - Will be set up during deployment

---

## 📱 **OPTIONAL (Enhanced Features)**

### 6. **Firebase Service Account** ⭐
- **File**: `firebase-service-account.json`
- **Get it from**: [Firebase Console](https://console.firebase.google.com/)
- **Usage**: 
  - Push notifications
  - Background task tracking
  - User management
- **Features Enabled**:
  - Real-time progress updates
  - Push notifications to users
  - Task status persistence
- **Status**: **OPTIONAL** - App works without it, but notifications disabled

---

## 🔍 **DEEP CODE ANALYSIS**

### **Environment Variables Used:**

```python
# From backend.py lines 118-146
GENAI_API_KEY = os.getenv("GENAI_API_KEY")           # Required
BASE_URL = os.getenv("BASE_URL")                     # Required
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")       # Required

# From main.py line 10
PORT = int(os.environ.get("PORT", 8080))             # Auto-set by Cloud Run
```

### **Google Cloud Services Used:**

1. **Google Generative AI** (`google-genai==1.24.0`)
   - Models: `gemini-2.5-flash-preview-04-17`, `gemini-2.5-pro`, `gemini-2.0-flash-preview-image-generation`
   - Functions: Text generation, image generation, comic creation

2. **Google Cloud Storage** (`google-cloud-storage>=2.10.0`)
   - Functions: Store images, audio files, assets
   - Access: Signed URLs (60-minute expiration)

3. **Google Cloud Text-to-Speech** (`google-cloud-texttospeech>=2.16.0`)
   - Functions: Generate audio for lectures
   - Voice: `en-US-Chirp3-HD-Aoede`

4. **Firebase Admin SDK** (`firebase-admin>=6.5.0`)
   - Functions: Push notifications, task tracking
   - Collections: `request_progress`, `background_tasks`

### **Authentication Methods:**

1. **Service Account Key** (Firebase)
   ```python
   cred = credentials.Certificate("firebase-service-account.json")
   ```

2. **Default Credentials** (Google Cloud)
   ```python
   storage_client = storage.Client()  # Uses default credentials
   tts_client = texttospeech.TextToSpeechClient()  # Uses default credentials
   ```

3. **API Key** (GenAI)
   ```python
   client = genai.Client(api_key=GENAI_API_KEY)
   ```

---

## 💰 **Cost Estimation**

| Service | Estimated Monthly Cost | Billing Model |
|---------|----------------------|---------------|
| **Cloud Run** | $10-30 | Pay-per-use |
| **Google AI API** | $5-50 | Pay-per-use |
| **Cloud Storage** | $1-5 | Pay-per-use |
| **Text-to-Speech** | $1-10 | Pay-per-use |
| **Firebase** | $0-5 | Free tier + pay-per-use |
| **Total** | **$15-100** | Varies by usage |

---

## 🚀 **Deployment Checklist**

### **Before Deployment:**
- [ ] Get Google Generative AI API key
- [ ] Enable billing on Google Cloud project
- [ ] Install gcloud CLI and authenticate

### **During Deployment:**
- [ ] Run `./deploy-cloud-run-fixed.sh`
- [ ] APIs will be auto-enabled
- [ ] GCS bucket will be auto-created
- [ ] Service account permissions will be auto-configured

### **After Deployment:**
- [ ] Update `GENAI_API_KEY` in Cloud Run environment variables
- [ ] Update `BASE_URL` with your service URL
- [ ] (Optional) Add Firebase service account for notifications

---

## 🔒 **Security Best Practices**

### **✅ Implemented:**
- Signed URLs for secure file access
- No public bucket access required
- Environment variables for secrets
- Service account with least privilege

### **⚠️ Important:**
- Never commit API keys to git
- Use Cloud Run secrets for sensitive data
- Monitor usage and set billing alerts
- Regularly rotate API keys

---

## 🧪 **Testing Your Setup**

### **Health Check:**
```bash
curl https://your-service-url/health
```

### **Test API Key:**
```bash
curl -X POST https://your-service-url/process \
  -H "Content-Type: application/json" \
  -d '{"input_text": "Hello world", "level": "moderate"}'
```

### **Test Image Generation:**
```bash
curl -X POST https://your-service-url/generate_image \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A cat sitting on a chair", "level": "moderate"}'
```

---

## 📞 **Support & Troubleshooting**

### **Common Issues:**
1. **"API key not found"** → Get GenAI API key from Google AI Studio
2. **"Bucket not found"** → Check GCS_BUCKET_NAME environment variable
3. **"Permission denied"** → Check service account IAM roles
4. **"Firebase not initialized"** → Add firebase-service-account.json (optional)

### **Useful Commands:**
```bash
# Check environment variables
gcloud run services describe liroo-backend --region us-central1 --format="value(spec.template.spec.containers[0].env[].name,spec.template.spec.containers[0].env[].value)"

# View logs
gcloud run services logs tail liroo-backend --region us-central1

# Check service status
gcloud run services describe liroo-backend --region us-central1
```

---

## 🎯 **Priority Order for Setup**

1. **🔥 CRITICAL**: Get Google Generative AI API key
2. **🔥 CRITICAL**: Deploy to Cloud Run (auto-sets most things)
3. **🔥 CRITICAL**: Update environment variables in Cloud Console
4. **⭐ IMPORTANT**: Test basic functionality
5. **⭐ OPTIONAL**: Add Firebase for notifications

**Total Setup Time**: ~30 minutes (mostly waiting for deployment) 