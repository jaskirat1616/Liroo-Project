import logging
import os
import re
import json
from io import BytesIO
from uuid import uuid4
from flask import Flask, request, jsonify
from flask_cors import CORS

from google.cloud import storage
from google.cloud import texttospeech
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import datetime
import hashlib
import uuid
<<<<<<< HEAD
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, List, Tuple
import time
=======
import time
import threading
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore, messaging
from google import genai
from google.genai import types
import base64
import gc
from google.oauth2 import service_account

# Try to import psutil for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("psutil not available - memory monitoring disabled")

# Memory management configuration
MEMORY_LIMIT_MB = 1500  # Set memory limit to 1.5GB to leave buffer
MEMORY_WARNING_MB = 1000  # Warning at 1GB
FORCE_GC_THRESHOLD_MB = 1200  # Force garbage collection at 1.2GB

def get_memory_usage():
    """Get current memory usage in MB"""
    if PSUTIL_AVAILABLE:
        process = psutil.Process()
        memory_info = process.memory_info()
        return memory_info.rss / 1024 / 1024
    return 0

def check_memory_and_cleanup():
    """Check memory usage and perform cleanup if needed"""
    memory_mb = get_memory_usage()
    
    if memory_mb > FORCE_GC_THRESHOLD_MB:
        logger.warning(f"High memory usage detected: {memory_mb:.1f} MB. Forcing garbage collection...")
        gc.collect()
        time.sleep(1)  # Give GC time to work
        memory_mb = get_memory_usage()
        logger.info(f"Memory after cleanup: {memory_mb:.1f} MB")
    
    if memory_mb > MEMORY_WARNING_MB:
        logger.warning(f"Memory usage is high: {memory_mb:.1f} MB")
    
    return memory_mb

def safe_image_processing(image_data_bytes, prompt):
    """Safely process image data with memory management"""
    try:
        # Check memory before processing
        initial_memory = get_memory_usage()
        logger.debug(f"Memory before image processing: {initial_memory:.1f} MB")
        
        if not isinstance(image_data_bytes, bytes):
            logger.error(f"Image data is not bytes, got type: {type(image_data_bytes)}")
            raise ValueError("Image data is not in bytes format")
        
        if len(image_data_bytes) < 1000:
            logger.warning(f"Image data too small ({len(image_data_bytes)} bytes) for prompt: {prompt}")
            raise ValueError("Image data too small to be a valid image")
        
        # Open and verify image
        image = Image.open(BytesIO(image_data_bytes))
        image.verify()
        
        # Reopen for processing
        image = Image.open(BytesIO(image_data_bytes))
        
        # Convert RGBA to RGB to save memory
        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            image = background
        
        # Optimize image size if too large
        max_size = (1024, 1024)  # Limit image size to save memory
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            logger.debug(f"Resized image to {image.size}")
        
        # Save to buffer with optimization
        buffer = BytesIO()
        image.save(buffer, format="PNG", optimize=True, compress_level=6)
        buffer.seek(0)
        
        # Clean up image objects
        del image
        gc.collect()
        
        # Check memory after processing
        final_memory = get_memory_usage()
        logger.debug(f"Memory after image processing: {final_memory:.1f} MB")
        
        return buffer
        
    except Exception as e:
        logger.error(f"Error in safe_image_processing: {e}")
        raise e
>>>>>>> 9129cfe4b41d693ce0501e8a686c17ac643b01c0

# Load environment
load_dotenv()
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
BASE_URL = os.getenv("BASE_URL")

# Initialize Firebase Admin SDK
try:
    # Try to initialize with service account key
    cred = credentials.Certificate("firebase-service-account.json")
    firebase_admin.initialize_app(cred)
    print("✅ Firebase Admin SDK initialized with service account")
except FileNotFoundError:
    try:
        # Try to initialize with default credentials (for cloud deployment)
        firebase_admin.initialize_app()
        print("✅ Firebase Admin SDK initialized with default credentials")
    except Exception as e:
        print(f"⚠️ Firebase Admin SDK initialization failed: {e}")
        print("⚠️ Push notifications will be disabled")

# Initialize Firestore
try:
    db = firestore.client()
    print("✅ Firestore client initialized")
except Exception as e:
    print(f"❌ Firestore client initialization failed: {e}")
    print("⚠️ Firebase functionality disabled - background notifications will not work")
    db = None

# GCS setup - Initialize lazily to handle authentication errors
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
storage_client = None
bucket = None

def initialize_gcs():
    """Initialize Google Cloud Storage client lazily"""
    global storage_client, bucket
    try:
        if storage_client is None:
            # Try to use service account key file first for proper signing capabilities
            try:
                cred = service_account.Credentials.from_service_account_file("firebase-service-account.json")
                storage_client = storage.Client(credentials=cred)
                print("✅ Google Cloud Storage client initialized with service account key")
            except FileNotFoundError:
                # Fall back to default credentials
                storage_client = storage.Client()
                print("✅ Google Cloud Storage client initialized with default credentials")
            except Exception as e:
                print(f"⚠️ Service account key failed, using default credentials: {e}")
                storage_client = storage.Client()
                print("✅ Google Cloud Storage client initialized with default credentials")
        if bucket is None and GCS_BUCKET_NAME:
            print(f"🔧 Attempting to access GCS bucket: {GCS_BUCKET_NAME}")
            bucket = storage_client.bucket(GCS_BUCKET_NAME)
            print(f"✅ GCS bucket '{GCS_BUCKET_NAME}' initialized")
        elif not GCS_BUCKET_NAME:
            print("⚠️ GCS_BUCKET_NAME environment variable not set")
            return False
        return True
    except Exception as e:
        print(f"❌ Google Cloud Storage initialization failed: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        print("⚠️ File storage functionality will be disabled")
        print("💡 Make sure the service account has the following roles:")
        print("   - Storage Object Admin (for uploading files)")
        print("   - Storage Object Viewer (for generating signed URLs)")
        return False

# Initialize Text-to-Speech client - Initialize lazily
tts_client = None

def initialize_tts():
    """Initialize Text-to-Speech client lazily"""
    global tts_client
    try:
        if tts_client is None:
            # Try to use service account key file first for consistency
            try:
                cred = service_account.Credentials.from_service_account_file("firebase-service-account.json")
                tts_client = texttospeech.TextToSpeechClient(credentials=cred)
                print("✅ Text-to-Speech client initialized with service account key")
            except FileNotFoundError:
                # Fall back to default credentials
                tts_client = texttospeech.TextToSpeechClient()
                print("✅ Text-to-Speech client initialized with default credentials")
            except Exception as e:
                print(f"⚠️ Service account key failed, using default credentials: {e}")
                tts_client = texttospeech.TextToSpeechClient()
                print("✅ Text-to-Speech client initialized with default credentials")
        return True
    except Exception as e:
        print(f"❌ Text-to-Speech client initialization failed: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        print("⚠️ Text-to-Speech functionality will be disabled")
        print("💡 Make sure the service account has the following roles:")
        print("   - Cloud Text-to-Speech User")
        return False

# GenAI client - configure only, models will be initialized after SYSTEM_INSTRUCTION
client = genai.Client(api_key=GENAI_API_KEY)

# Image generation models - with fallback chain
PRIMARY_IMAGE_MODEL = "gemini-3.0-pro-exp"  # Latest with Nano Banana Pro features
FALLBACK_IMAGE_MODEL = "gemini-2.5-flash-image"  # Fast fallback
LEGACY_IMAGE_MODEL = "gemini-2.0-flash-exp-image-generation"  # Last resort

# Thread pool for async image generation
image_executor = ThreadPoolExecutor(max_workers=5)

# Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Flask setup
app = Flask(__name__)
CORS(app, resources={r"/process": {"origins": ["http://localhost:3000","*"]}})

# Add progress tracking for each request
request_progress = {}  # Store progress for each request
request_start_times = {}  # Store start times for each request
request_data = {}  # Store request data for persistence
request_user_tokens = {}  # Store user FCM tokens for notifications

def update_request_progress(request_id, step, step_number, total_steps, details=""):
    """Update progress for a specific request"""
    if request_id in request_progress:
        request_progress[request_id].update({
            'step': step,
            'step_number': step_number,
            'total_steps': total_steps,
            'details': details,
            'last_updated': datetime.now().isoformat(),
            'progress_percentage': min((step_number / total_steps) * 100, 100)
        })
        print(f"[Progress] Request {request_id}: {step_number}/{total_steps} - {step} - {details}")
        
        # Update Firebase if available
        if db:
            try:
                db.collection('request_progress').document(request_id).set({
                    'step': step,
                    'step_number': step_number,
                    'total_steps': total_steps,
                    'details': details,
                    'last_updated': datetime.now().isoformat(),
                    'progress_percentage': min((step_number / total_steps) * 100, 100),
                    'status': 'processing'
                }, merge=True)
            except Exception as e:
                logger.error(f"Failed to update Firebase progress: {e}")
        else:
            logger.debug(f"Firebase disabled - skipping progress update for {request_id}")

def get_request_progress(request_id):
    """Get current progress for a request"""
    return request_progress.get(request_id, {})

def cleanup_request_progress(request_id):
    """Clean up progress data for a completed request"""
    if request_id in request_progress:
        del request_progress[request_id]
    if request_id in request_start_times:
        del request_start_times[request_id]
    if request_id in request_data:
        del request_data[request_id]
    if request_id in request_user_tokens:
        del request_user_tokens[request_id]
    
    # Clean up from Firebase
    if db:
        try:
            db.collection('request_progress').document(request_id).delete()
        except Exception as e:
            logger.error(f"Failed to cleanup Firebase progress: {e}")
    else:
        logger.debug(f"Firebase disabled - skipping cleanup for {request_id}")

def send_push_notification(user_token, title, body, data=None):
    """Send push notification to user"""
    if not user_token:
        logger.warning("No user token provided for push notification")
        return False
    
    if not firebase_admin._apps:
        logger.warning("Firebase not initialized - push notifications disabled")
        return False
    
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data or {},
            token=user_token
        )
        
        response = messaging.send(message)
        logger.info(f"✅ Push notification sent successfully: {response}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send push notification: {e}")
        return False

def update_firebase_task_status(request_id, status, result_data=None, error_message=None):
    """Update task status in Firebase for background completion tracking"""
    if not db:
        logger.warning("Firestore not available for status update")
        return False
    
    try:
        update_data = {
            'status': status,
            'last_updated': datetime.now().isoformat(),
            'completed_at': datetime.now().isoformat() if status in ['completed', 'failed'] else None
        }
        
        if result_data:
            update_data['result_data'] = result_data
        
        if error_message:
            update_data['error_message'] = error_message
        
        db.collection('background_tasks').document(request_id).set(update_data, merge=True)
        logger.info(f"✅ Firebase task status updated: {request_id} - {status}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to update Firebase task status: {e}")
        return False




@app.route('/memory', methods=['GET'])
def memory_status():
    """Detailed memory status endpoint for monitoring"""
    try:
        memory_mb = get_memory_usage()
        
        # Get additional memory info if psutil is available
        memory_details = {}
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_details = {
                "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                "percent": round(process.memory_percent(), 2)
            }
        
        return jsonify({
            "memory_usage_mb": round(memory_mb, 2),
            "memory_warning_threshold_mb": MEMORY_WARNING_MB,
            "memory_limit_mb": MEMORY_LIMIT_MB,
            "memory_status": "normal" if memory_mb < MEMORY_WARNING_MB else "warning" if memory_mb < MEMORY_LIMIT_MB else "critical",
            "memory_details": memory_details,
            "psutil_available": PSUTIL_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Memory status check failed: {e}")
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# Testing
@app.route('/')
def home():
    return jsonify({"status": "ok", "message": "Server is running"})

# Define Reading Levels for clarity
READING_LEVELS = {
    "beginner": "Simple vocabulary, very short sentences, lots of examples, explain concepts very basically (ages 6-10).",
    "moderate": "Slightly more complex words (defined simply), short to medium sentences, clear examples (ages 10-13).",
    "intermediate": "Standard vocabulary, varied sentence length, relatable examples, assume some prior knowledge but explain key terms (ages 13-18)."
}

# Add after READING_LEVELS definition
STORY_GENRES = {
    "Adventure": "Create an exciting journey with challenges and discoveries. Include elements of exploration, action, and personal growth.",
    "Fantasy": "Incorporate magical elements, mythical creatures, or supernatural powers. Create a world with its own rules and wonders.",
    "Mystery": "Build suspense and intrigue. Include clues, puzzles, and a central question that needs solving.",
    "Science Fiction": "Focus on scientific concepts, futuristic technology, or space exploration. Consider the impact of science on society.",
    "Historical": "Set the story in a specific historical period. Include accurate historical details while making the narrative engaging.",
    "Educational": "Focus on teaching concepts through narrative. Make learning fun and memorable through storytelling."
}

# System instruction - UPDATED
beginner_Desc = READING_LEVELS["beginner"]
moderate_Desc = READING_LEVELS["moderate"]
intermediate_Desc = READING_LEVELS["intermediate"]

SYSTEM_INSTRUCTION = f"""You are an expert assistant creating educational content for kids and young adults, especially those with dyslexia. Your main goal is to take a text input and transform it into a response that is clear, engaging, comprehensive, and easy for the user to understand, tailored to their specified reading level, desired summarization tier, and profile.

**Reading Level Guidance:**

The user will provide a reading level. Adapt your language, sentence structure, examples, and depth of explanation accordingly:
*   **beginner:** {beginner_Desc}
*   **moderate:** {moderate_Desc}
*   **intermediate:** {intermediate_Desc}


**Summarization Tier Guidance:**

The user will also specify a summarization tier. Adapt your output length and focus accordingly:
*   **Detailed Explanation:** This is the default behavior. Provide a comprehensive explanation as per the general instructions.

**Profile-Driven Personalization (CRUCIAL FOR EFFECTIVE EXPLANATIONS):**

You will receive user profile information formatted like `[Profile: Student Level={{student_level}}, Interests={{topics_of_interest}}]`.
This information is NOT optional; you MUST use it to tailor your explanations:

*   **Adapt to Student Level:**
    *   If `studentLevel` is provided (e.g., 'High School', 'University'), your analogies, examples, vocabulary, and the depth of explanation MUST be directly relatable and appropriate for that age group's typical experiences, knowledge base, and curriculum.
    *   For example: If `studentLevel` is 'High School', ensure analogies are relatable to common high school subjects or typical teenage experiences, and simplify complex terms accordingly. If 'University', examples can be more academic, draw from higher-level concepts, or be more abstract.

*   **Integrate Topics of Interest:**
    *   If `topicsOfInterest` are provided (e.g., 'history', 'science', 'art'), you MUST actively seek opportunities to weave relevant examples, perspectives, or connections from these interest areas into your explanation of the *current topic*.
    *   For example: If explaining a physics concept and the user's `topicsOfInterest` include 'history', you MUST try to use historical examples, such as mentioning a key historical figure or discovery related to that physics concept. If explaining literature and the user's interest is 'science', you could draw parallels to scientific methods or discoveries if applicable.

*   **Natural and Purposeful Integration:**
    *   Integrate these profile-driven examples and adaptations smoothly and naturally. They should clearly enhance understanding and engagement, not feel forced or irrelevant.
    *   If a particular interest doesn't directly align with the topic in a way that aids explanation, prioritize a clear explanation of the topic itself, but still adapt thoroughly to the `studentLevel`.

*   **Non-Negotiable Influence:** This personalization is not a suggestion. It MUST STRONGLY and demonstrably influence your choice of examples, analogies, and the overall framing of the explanation. The goal is content that feels personally tailored to the user.

---

### Instructions for Creating Clear and Engaging Educational Content (Apply Level and Profile Appropriately)

**(These instructions primarily apply to the "Detailed Explanation" tier. )**

**SPECIAL INTRODUCTORY GHIBLI-STYLE IMAGE (Detailed Explanation Tier Only):**
*   **As the VERY FIRST element of your response, before any headings or text, include ONE special image placeholder: `[GhibliImage: A concise, evocative description for a Studio Ghibli-style illustration that visually summarizes the entire topic. This image should be beautiful and artistic, setting the tone.]`**
*   Example: If the topic is "The Ocean's Wonders", a good GhibliImage description might be `[GhibliImage: A breathtaking Studio Ghibli style panorama of a vibrant coral reef teeming with whimsical sea creatures, light rays filtering through turquoise water, conveying a sense of magic and discovery.]`
*   Do NOT include any other text or explanation around this `[GhibliImage: ...]` tag itself. It must be the first line.

1.  **Use Clear and Accessible Language (Level-Adjusted)**
    *   Write in clear sentences appropriate for the level. Vary sentence length for flow, but keep it generally shorter for lower levels.
    *   Use vocabulary common for the target age group.
    *   **Explain Necessary Terms**: Define complex or important words simply, especially for lower levels. The complexity of the term itself depends on the level.
    *   Use active voice where possible.

2.  **Structure for Understanding**
    *   Break text into focused paragraphs appropriate for the level's attention span.
    *   Use clear, bold headings with **asterisks** (e.g., **Why is Space Travel Hard?**) to introduce new sections.
    *   Use bullet points or numbered lists for steps, examples, or key points.
    *   Ensure a logical flow.

3.  **Focus on Explanation and Comprehension (Level-Adjusted)**
    *   **Explain Thoroughly**: Explain the 'why' and 'how' to a depth appropriate for the level. Avoid oversimplifying for higher levels if it loses meaning.
    *   **Use Analogies and Examples**: Use analogies and examples relevant to the target age group's experience.
    *   **Visual Support (Static Images)**: Include `[Image: Description]` placeholders where a picture would significantly help explain or engage. Describe the image's purpose clearly. These are for static illustrations.
    *   **Repeat Key Ideas Gently**: Restating important points can help, especially for lower levels.

4.  **Maintain Dyslexia-Friendly Formatting**
    *   Keep text left-aligned.
    *   Use bolding (`**text**`) for emphasis on key terms *after* they've been introduced/defined, or for headings. Use italics (`*text*`) sparingly.
    *   Use white space (paragraph breaks) effectively.

5.  **Engaging and Encouraging Tone (Level-Adjusted)**
    *   Use a positive, friendly tone suitable for the age group.
    *   Directly address the reader ("you").
    *   Ask occasional rhetorical questions relevant to the level.
    *   Celebrate learning.

6.  **Image Prompts (Regular Content Images for Detailed Explanation)**
    *   After the initial `[GhibliImage: ...]` placeholder, include at least **two** more regular `[Image: Description]` placeholders per response for the "Detailed Explanation" tier. These are for illustrating specific points within the text.
    *   Make descriptions clear and related to the text.

7.  **Quiz or Test (Level-Adjusted for Detailed Explanation)**
    *   Include a short quiz (3-10 questions) at the end depending on the content length. Adjust question complexity and format (multiple choice, short answer, T/F) based on the level.
    *   **Follow Quiz Formatting Guidelines below.**


---

### Quiz Formatting Guidelines (IMPORTANT for Parsing):

When creating a quiz at the end of the content, please follow this format strictly:

1.  **Quiz Header**: Start the quiz section with a heading like `**Quiz Time!**` or `**Test Your Knowledge**`.
2.  **Questions**:
    *   Each question should start on a new line, numbered (e.g., `1. Question text?`).
    *   Options should follow, each on a new line, prefixed with a letter and a parenthesis (e.g., `a) Option A`, `b) Option B`).
    *   The correct answer should be indicated on a new line as `Correct Answer: [letter]` (e.g., `Correct Answer: b`).
    *   An optional explanation should follow on a new line as `Explanation: [text]` (e.g., `Explanation: This is because...`).
    *   Leave a blank line between the end of one question's explanation (or its correct answer line if no explanation) and the start of the next numbered question.

**Example Quiz Question Format:**

**Quiz Time!**

1.  What is the main color of the sun?
    a) Blue
    b) Yellow
    c) Green
    Correct Answer: b
    Explanation: The sun emits light across many wavelengths, but it appears yellow to us.

2.  How many planets are in our solar system?
    a) 7
    b) 8
    c) 9
    Correct Answer: b
    Explanation: Pluto was reclassified as a dwarf planet.

---

### Task: Processing Text Input

When given input text (which might be prefixed with level and tier info like `[Level: moderate] [Summary Tier: Quick Summary]`), follow these steps:

1.  **Identify Level and Summarization Tier**: Note the specified reading level and summarization tier from the input.
2.  **Understand and Summarize (Tier-Dependent)**:
    *   For "Detailed Explanation": Read the input to grasp the main topic. Start your response with a brief, engaging introduction (2-3 sentences) suitable for the level. Then proceed with detailed content.
    *   
    *   
3.  **Organize (Tier-Dependent)**:
    *   For "Detailed Explanation": Structure the information logically using **bold headings**.
    *   
4.  **Rewrite and Explain (Tier-Dependent)**:
    *   For "Detailed Explanation": Rewrite the content following all instructions above (including Image and InteractiveChart placeholders), critically adapting to the specified reading level.
    *   
5.  **Integrate Visuals (Tier-Dependent)**:
    *   For "Detailed Explanation": Add `[Image: Description]` placeholders strategically (at least three).` placeholders if applicable.
    *   
6.  **Conclude Positively (Tier-Dependent)**:
    *   For "Detailed Explanation": End with a short, encouraging summary or thought-provoking question appropriate for the level.
    *   
7.  **Add Quiz (Tier-Dependent)**:
    *   For "Detailed Explanation": Include a short quiz tailored to the reading level, strictly following the Quiz Formatting Guidelines.
    *   
---

### Final Goal

Create content that truly *teaches* information in a way that is accessible, understandable, and engaging for the user's specified reading level and summarization tier, especially considering potential reading challenges. Ensure explanations are sufficient for genuine understanding at that level. For "Detailed Explanation", add at least three `[Image: Description]` placeholders, potentially `[InteractiveChart: ...]` placeholders, and a quiz. For other tiers, strictly adhere to their format. Go for it!
"""

EXPLAIN_AGAIN_PROMPT_TEMPLATE = """You are an expert at rephrasing and clarifying text for better understanding.
The user has requested an alternative explanation for the following paragraph.
Your task is to re-explain this paragraph in a different way, using simpler terms, different examples, or a new perspective, while strictly adhering to the user's specified reading level and profile context.
The goal is to provide a fresh explanation that might click better for the user if the original did not.
Do NOT add any extra conversational text, headings, or any formatting other than the re-explained paragraph itself.

**User's Reading Level:** {level}
**User's Profile Context:** {profile_context_str}

**Original Paragraph to Re-explain:**
---
{original_paragraph}
---

**Re-explained Paragraph (keeping the same core meaning but explained differently):**
"""

# *** NEW: DIALOGUE PROMPT TEMPLATE ***
DIALOGUE_PROMPT_TEMPLATE = """You are an expert AI Conversational Tutor for Liroo. Your goal is to help users deeply understand a specific piece of text they are curious about.
The user has selected a piece of text from a larger content block and has initiated a dialogue with you.

**User's Reading Level:** {level}
**User's Profile Context:** {profile_context_str}

**Original Content Block (for broader context):**
---
{original_block_content}
---

**Selected Text/Concept the user wants to discuss:**
---
{selected_text_snippet}
---

**Current Conversation History (User and your previous responses):**
---
{conversation_history}
---

**User's Latest Question/Prompt:**
---
{user_question}
---

**Your Task:**
Respond to the user's latest question/prompt. Your response MUST:
1.  **Be Conversational:** Engage the user in a natural, helpful, and encouraging dialogue.
2.  **Stay Focused:** Directly address the user's question in relation to the `selected_text_snippet` and the `original_block_content`.
3.  **Use Socratic Questioning (When Appropriate):** Instead of always giving direct answers, guide the user to deeper understanding by asking thought-provoking questions. Examples: "What are your initial thoughts on why that might be?", "How do you think this connects to what we discussed earlier about X?", "What would happen if Y was different in this context?".
4.  **Offer Elaboration/Simplification/Analogies:** Be ready to explain concepts in different ways if the user is confused. You can offer:
    *   "Would you like me to explain that in simpler terms?"
    *   "I can give you another example if that would help."
    *   "Think of it like this: [analogy relevant to their reading level and interests]."
5.  **Maintain Context:** Remember previous parts of THIS current dialogue session (from `conversation_history`).
6.  **Adhere to Reading Level and Profile:** All explanations, examples, and questions MUST be tailored to the user's specified `level` and `profile_context_str`.
7.  **Be Concise yet Comprehensive:** Provide enough information to be helpful, but avoid overly long responses that might overwhelm the user. Aim for 1-3 paragraphs per turn unless more is truly needed.
8.  **Do NOT repeat the boilerplate "User's Reading Level", "Original Content Block", etc. in your response.** Just provide your conversational reply to the user.
9.  **If the user's question seems unrelated or you're unsure, gently try to guide them back to the selected text or ask for clarification.**

Respond directly to the user's question now:
"""

# *** NEW: Flashcard Prompt Template ***
FLASHCARD_PROMPT_TEMPLATE = """You are an expert at creating educational flashcards.
Given the following text, your task is to extract key concepts and create a list of flashcards.
Each flashcard should have a 'front' (the term or question) and a 'back' (the definition or answer).
Ensure the content is appropriate for the user's reading level and profile context.
**Generate between 3-10 flashcards based on the content length - create more cards for longer texts and fewer for shorter ones. No less than 3 cards and no more than 10 cards exactly.If the input is truly empty, return an array with a single flashcard saying 'No content provided.'**
Output the flashcards as a JSON array of objects, where each object has 'front' and 'back' keys.
**Important JSON Formatting Rules:**
1. The entire output MUST be a single, valid JSON array.
2. All string values (e.g., for 'front' and 'back' keys) must be correctly formatted JSON strings. This means any literal newline characters within the text content MUST be escaped as '\\n'. For example, if a flashcard back has two lines, it should be represented like "Line 1\\nLine 2".
3. Do NOT include any other text, explanation, or formatting outside this JSON array.

User's Reading Level: {level}
User's Profile Context: {profile_context_str}

Input Text:
---
{input_text}
---

JSON Output:
"""

# *** NEW: Slideshow Prompt Template ***
SLIDESHOW_PROMPT_TEMPLATE = """You are an expert at summarizing educational content into a structured slideshow format.
Given the following text, your task is to break it down into a few key slides depending on the content length (typically 6-10).
Each slide should have an optional title and a list of bullet points summarizing the content for that slide.
Ensure the content is appropriate for the user's reading level and profile context.
**You must always generate at least 3 slides, even if you have to repeat or rephrase information. If the input is truly empty, return an array with a single slide whose content is ['No content provided.'].**
Output the slideshow as a JSON array of objects, where each object has an optional 'title' (string or null) and a 'content' key (an array of strings for bullet points).
**Important JSON Formatting Rules:**
1. The entire output MUST be a single, valid JSON array.
2. All string values (e.g., for 'title' or items in the 'content' array) must be correctly formatted JSON strings. This means any literal newline characters within the text content MUST be escaped as '\\n'. For example, if a bullet point has two lines, it should be represented like "Line 1\\nLine 2".
3. Do NOT include any other text, explanation, or formatting outside this JSON array.

User's Reading Level: {level}
User's Profile Context: {profile_context_str}

Input Text:
---
{input_text}
---

JSON Output:
"""

# *** NEW: Lecture Generation Prompt Template ***
LECTURE_GENERATION_PROMPT_TEMPLATE = """You are a smart, casual, and friendly AI teacher.

Turn the following academic or article text into a spoken lecture.
Break it down into 3-5 sections.
For each section, provide:
- A catchy section title
- A clear and casual script that explains the concept
- A detailed image prompt to generate an illustration or diagram

Format the output as JSON with this structure:

{{
  "title": "...",
  "sections": [
    {{
      "title": "...",
      "script": "...",
      "image_prompt": "..."
    }},
    ...
  ]
}}

Text:
\"\"\"{text}\"\"\"
"""

# Story Generation Instruction
STORY_GENERATION_INSTRUCTION = """You are an expert storyteller creating engaging educational content. Your task is to transform the given text into a story that:
1. Maintains all key educational information from the original text
2. Presents it in an engaging narrative format
3. Adapts to the specified reading level
4. Incorporates the chosen genre's style and elements
5. Features the main character (if provided) as the protagonist
6. Uses appropriate vocabulary and sentence structure for the reading level
7. Includes descriptive elements that make the story vivid and memorable
8. Creates a natural flow that makes learning enjoyable

For each genre, follow these specific guidelines:
{genre_guidelines}

For reading levels, adapt your language and complexity:
- beginner: Simple vocabulary, very short sentences, lots of examples
- moderate: Slightly more complex words (defined simply), short to medium sentences
- intermediate: Standard vocabulary, varied sentence length, relatable examples

Remember to:
- Keep the educational value of the original text
- Make the story engaging and memorable
- Use appropriate pacing for the reading level
- Include sensory details that bring the story to life
- Create a clear narrative arc with beginning, middle, and end
"""

# Initialize GenAI models after SYSTEM_INSTRUCTION is defined


def text_to_speech(text: str, filename: str, voice_name: str = "en-US-Chirp3-HD-Aoede") -> bool:
<<<<<<< HEAD
    """
    Convert text to speech using Google Cloud TTS with Chirp3 HD voices.
    
    This function uses high-quality Chirp3 HD voices optimized for narration.
    The default voice (Aoede) is warm and friendly, perfect for reading stories
    to children, like a parent reading a bedtime story.
    
    Args:
        text: The text to convert to speech
        filename: Output file path for the audio
        voice_name: Voice to use (default: en-US-Chirp3-HD-Aoede for narrator)
    
    Returns:
        True if successful, False otherwise
    """
=======
    """Convert text to speech and save as MP3 file."""
>>>>>>> 9129cfe4b41d693ce0501e8a686c17ac643b01c0
    try:
        # Initialize TTS client if needed
        if not initialize_tts():
            logger.error("❌ TTS client not available")
            return False
            
        # Create the text input
        synthesis_input = texttospeech.SynthesisInput(text=text)

<<<<<<< HEAD
        # Build the voice request with Chirp3 HD voice
        # Chirp3 HD voices are high-quality, natural-sounding voices
=======
        # Build the voice request
>>>>>>> 9129cfe4b41d693ce0501e8a686c17ac643b01c0
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=voice_name
        )

<<<<<<< HEAD
        # Select the type of audio file you want returned
        # Optimized settings for storytelling/narration:
=======
        # Select the type of audio file to return
>>>>>>> 9129cfe4b41d693ce0501e8a686c17ac643b01c0
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,  # Normal speed (good for stories)
            pitch=0.0,  # Normal pitch
            volume_gain_db=0.0  # Normal volume
        )

        # Perform the text-to-speech request
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # Write the response to an audio file
        with open(filename, "wb") as out:
            out.write(response.audio_content)

        logger.info(f"🔊 Audio content written to file: {filename} (voice: {voice_name})")
        return True

    except Exception as e:
        logger.error(f"❌ Error generating TTS for {filename}: {str(e)}")
        return False

def generate_lecture_script(text: str) -> str:
    """Generate a lecture script from input text."""
    prompt = LECTURE_GENERATION_PROMPT_TEMPLATE.format(text=text[:8000])
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION
            )
        )
        return response.text
    except Exception as e:
        logger.error(f"Error generating lecture script: {e}")
        return None

def clean_lecture_json_string(json_str: str) -> str:
    """Removes markdown code fences and trims whitespace."""
    if not json_str:
        return "{}"
        
    json_str = json_str.strip()
    if json_str.startswith("```json"):
        json_str = json_str[len("```json"):].strip()
    elif json_str.startswith("```"):
        json_str = json_str[len("```"):].strip()
    if json_str.endswith("```"):
        json_str = json_str[:-3].strip()

    # Clean up multi-line strings in image prompts by normalizing whitespace
    import re
    # Replace multiple whitespace characters (including newlines) with single spaces
    # but preserve the JSON structure
    json_str = re.sub(r'\s+', ' ', json_str)

    return json_str

def generate_lecture_audio_and_images(lecture_json_text: str, level: str = "moderate", image_style: str = None):
    """Generate audio files and images for a lecture."""
    cleaned_text = clean_lecture_json_string(lecture_json_text)

    try:
        lecture_data = json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON output: {str(e)}")
        logger.info("Attempting alternative parsing...")

        # Alternative approach: try to fix common JSON issues
        try:
            # Remove problematic characters that might break JSON
            import re

            # Method 1: Simple whitespace normalization
            normalized_text = re.sub(r'\s+', ' ', cleaned_text)
            lecture_data = json.loads(normalized_text)
            logger.info("Successfully parsed with whitespace normalization!")

        except json.JSONDecodeError:
            try:
                # Method 2: Fix potential quote escaping issues
                quote_fixed = cleaned_text.replace('\n', ' ').replace('\r', ' ')
                # Remove extra spaces around colons and commas
                quote_fixed = re.sub(r'\s*:\s*', ': ', quote_fixed)
                quote_fixed = re.sub(r'\s*,\s*', ', ', quote_fixed)
                lecture_data = json.loads(quote_fixed)
                logger.info("Successfully parsed with quote fixing!")

            except json.JSONDecodeError:
                logger.error("All parsing attempts failed. Raw output:")
                logger.error(cleaned_text[:500] + "..." if len(cleaned_text) > 500 else cleaned_text)
                return None

    # Generate unique filenames for audio files
    lecture_id = str(uuid4())
    audio_files = []
    
    # Generate TTS for the main title
    main_title = lecture_data.get("title", "Lecture")
    title_audio_filename = f"lecture_{lecture_id}_title.mp3"
    logger.info(f"Generating TTS for title: {main_title}")
    
    if text_to_speech(main_title, title_audio_filename, "en-US-Chirp3-HD-Autonoe"):
        # Upload to GCS using helper function
        signed_url = upload_to_gcs(title_audio_filename, f"audio/{title_audio_filename}", "audio/mpeg")
        
        if signed_url:
            audio_files.append({
                "type": "title",
                "text": main_title,
                "url": signed_url,
                "filename": title_audio_filename
            })
        
        # Clean up local file
        os.remove(title_audio_filename)

    # Process each section
    for i, section in enumerate(lecture_data.get("sections", []), start=1):
        section_title = section.get("title", f"Section {i}")
        script = section.get("script", "")
        prompt = section.get("image_prompt", "")

        logger.info(f"Processing Section {i}: {section_title}")

        # Generate TTS for section title
        if section_title:
            title_filename = f"lecture_{lecture_id}_section_{i}_title.mp3"
            logger.info(f"Generating TTS for section title...")
            if text_to_speech(section_title, title_filename, "en-US-Chirp3-HD-Autonoe"):
                # Upload to GCS using helper function
                signed_url = upload_to_gcs(title_filename, f"audio/{title_filename}", "audio/mpeg")
                
                if signed_url:
                    audio_files.append({
                        "type": "section_title",
                        "text": section_title,
                        "url": signed_url,
                        "filename": title_filename,
                        "section": i
                    })
                
                # Clean up local file
                os.remove(title_filename)

        # Generate TTS for section script
        if script:
            script_filename = f"lecture_{lecture_id}_section_{i}_script.mp3"
            logger.info(f"Generating TTS for section script...")
            if text_to_speech(script, script_filename, "en-US-Chirp3-HD-Autonoe"):
                # Upload to GCS using helper function
                signed_url = upload_to_gcs(script_filename, f"audio/{script_filename}", "audio/mpeg")
                
                if signed_url:
                    audio_files.append({
                        "type": "section_script",
                        "text": script,
                        "url": signed_url,
                        "filename": script_filename,
                        "section": i
                    })
                
                # Clean up local file
                os.remove(script_filename)

        # Generate image for section
        if prompt:
            logger.info(f"Generating image for section {i}: {prompt[:100]}...")

            try:
                filename = generate_unique_image_filename(
                    prompt, 
                    level=level, 
                    style_hint=image_style, 
                    prefix=f"lecture_{lecture_id}_section_{i}"
                )
                signed_url = generate_and_save_image(prompt, filename, level=level, style_hint=image_style)
                
                if signed_url:
                    section['image_url'] = signed_url
                    logger.info(f"Generated image for section {i}: {filename}")
                else:
                    logger.warning(f"Failed to generate image for section {i}")
                    
            except Exception as e:
                logger.error(f"Error generating image for section {i}: {str(e)}")
        else:
            logger.warning(f"Section {i} missing image prompt.")

    return {
        "lecture_data": lecture_data,
        "audio_files": audio_files,
        "lecture_id": lecture_id
    }

# ============================================================================
# Consistency Manager - Maintains visual consistency across images
# ============================================================================

class ConsistencyManager:
    """Manages visual consistency for characters, styles, and themes across images."""
    
    def __init__(self):
        # Store character/style references: {story_id: {character_name: description, style: info}}
        self.character_registry: Dict[str, Dict[str, any]] = {}
        self.style_registry: Dict[str, Dict[str, any]] = {}
        
    def register_character(self, story_id: str, character_name: str, description: str, reference_url: Optional[str] = None):
        """Register a character for consistency across story chapters."""
        if story_id not in self.character_registry:
            self.character_registry[story_id] = {}
        self.character_registry[story_id][character_name] = {
            "description": description,
            "reference_url": reference_url,
            "created_at": datetime.datetime.now().isoformat()
        }
        logger.info(f"Registered character '{character_name}' for story {story_id}")
    
    def get_character_reference(self, story_id: str, character_name: str) -> Optional[Dict]:
        """Get character reference for consistency."""
        if story_id in self.character_registry:
            return self.character_registry[story_id].get(character_name)
        return None
    
    def register_style(self, content_id: str, style_name: str, style_info: Dict):
        """Register a visual style for consistency across content blocks."""
        if content_id not in self.style_registry:
            self.style_registry[content_id] = {}
        self.style_registry[content_id][style_name] = {
            **style_info,
            "created_at": datetime.datetime.now().isoformat()
        }
        logger.info(f"Registered style '{style_name}' for content {content_id}")
    
    def get_style_reference(self, content_id: str, style_name: str) -> Optional[Dict]:
        """Get style reference for consistency."""
        if content_id in self.style_registry:
            return self.style_registry[content_id].get(style_name)
        return None
    
    def build_consistency_prompt(self, base_prompt: str, story_id: Optional[str] = None, 
                                 character_name: Optional[str] = None, 
                                 content_id: Optional[str] = None,
                                 style_name: Optional[str] = None) -> str:
        """Build enhanced prompt with consistency references."""
        enhanced = base_prompt
        
        # Add character consistency
        if story_id and character_name:
            char_ref = self.get_character_reference(story_id, character_name)
            if char_ref:
                enhanced = f"Maintain consistent character appearance: {char_ref['description']}. {enhanced}"
                if char_ref.get('reference_url'):
                    enhanced += f" Reference the visual style from: {char_ref['reference_url']}"
        
        # Add style consistency
        if content_id and style_name:
            style_ref = self.get_style_reference(content_id, style_name)
            if style_ref:
                enhanced = f"Maintain consistent visual style: {style_ref.get('description', style_name)}. {enhanced}"
        
        return enhanced

# Global consistency manager instance
consistency_manager = ConsistencyManager()

# ============================================================================
# Image Generation Service - Handles caching, async generation, and optimization
# ============================================================================

class ImageGenerationService:
    """Service for managing image generation with caching and performance optimization."""
    
    def __init__(self):
        # Simple in-memory cache: {prompt_hash: (url, timestamp)}
        self.image_cache: Dict[str, Tuple[str, float]] = {}
        self.cache_ttl = 3600  # 1 hour cache TTL
        
    def _get_cache_key(self, prompt: str, level: str, style_hint: Optional[str], 
                       aspect_ratio: Optional[str] = None) -> str:
        """Generate cache key from prompt and parameters."""
        key_parts = [prompt, level, style_hint or "", aspect_ratio or ""]
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode('utf-8')).hexdigest()
    
    def get_cached_image(self, prompt: str, level: str, style_hint: Optional[str],
                        aspect_ratio: Optional[str] = None) -> Optional[str]:
        """Check if image exists in cache."""
        cache_key = self._get_cache_key(prompt, level, style_hint, aspect_ratio)
        if cache_key in self.image_cache:
            url, timestamp = self.image_cache[cache_key]
            # Check if cache entry is still valid
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for prompt: {prompt[:50]}...")
                return url
            else:
                # Expired, remove from cache
                del self.image_cache[cache_key]
        return None
    
    def cache_image(self, prompt: str, level: str, style_hint: Optional[str],
                   url: str, aspect_ratio: Optional[str] = None):
        """Cache generated image URL."""
        cache_key = self._get_cache_key(prompt, level, style_hint, aspect_ratio)
        self.image_cache[cache_key] = (url, time.time())
        logger.debug(f"Cached image for prompt: {prompt[:50]}...")
    
    async def generate_images_async(self, prompts: List[Tuple[str, str]], 
                                   level: str, style_hint: Optional[str] = None) -> List[Optional[str]]:
        """Generate multiple images asynchronously."""
        loop = asyncio.get_event_loop()
        tasks = []
        
        for prompt, filename in prompts:
            task = loop.run_in_executor(
                image_executor,
                generate_and_save_image,
                prompt, filename, 2, level, style_hint
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Convert exceptions to None
        return [r if not isinstance(r, Exception) else None for r in results]

# Global image generation service instance
image_service = ImageGenerationService()

def generate_unique_image_filename(prompt, level=None, style_hint=None, prefix=None):
    base = f"{prompt}|{level or ''}|{style_hint or ''}"
    prompt_hash = hashlib.sha256(base.encode('utf-8')).hexdigest()[:10]
    uuid_part = uuid4().hex
    prefix = prefix or "img"
    return f"{prefix}_{prompt_hash}_{uuid_part}.png"

def create_placeholder_image(prompt, style_hint=None):
    output_filename = generate_unique_image_filename(prompt, style_hint=style_hint, prefix="placeholder")
    logger.debug(f"Creating placeholder for '{prompt}' as '{output_filename}'")
    try:
        image = Image.new('RGB', (512, 512), color='lightblue')
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("Arial.ttf", 20)
        except IOError:
            logger.warning("Arial.ttf not found, using default PIL font.")
            font = ImageFont.load_default()

        max_chars_line = 40
        wrapped_prompt = f"Placeholder:\n{prompt}"
        lines = []
        current_line = ""
        for word in wrapped_prompt.split():
            if len(current_line) + len(word) + 1 <= max_chars_line:
                current_line += f" {word}" if current_line else word
            else:
                lines.append(current_line.strip())
                current_line = word
        lines.append(current_line.strip())
        text = "\n".join(lines)

        # Clean text to avoid Unicode encoding issues
        text = text.encode('ascii', 'ignore').decode('ascii')

        bbox = draw.textbbox((0, 0), text, font=font, align="center")
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        pos = ((512 - text_width) // 2, (512 - text_height) // 2)

        draw.text(pos, text, fill='black', font=font, align="center")

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        
        # Upload to GCS using helper function
        signed_url = upload_buffer_to_gcs(buffer, f"images/{output_filename}", "image/png")
        
        if signed_url:
            logger.info(f"Placeholder image uploaded to GCS: {output_filename}")
            logger.debug(f"Generated signed URL (placeholder): {signed_url[:80]}...")
            return signed_url
        else:
            logger.error("Failed to upload placeholder image to GCS")
            return None
    except Exception as e:
        logger.error(f"Error creating placeholder: {e}")
        return None

<<<<<<< HEAD
def generate_and_save_image(prompt, output_filename=None, retries=2, level="Standard", 
                           style_hint=None, aspect_ratio=None, consistency_prompt=None,
                           story_id=None, character_name=None, use_cache=True):
    """Generate image with enhanced models, caching, and consistency support."""
    logger.debug(f"Generating image for '{prompt}' with style_hint: {style_hint}, aspect_ratio: {aspect_ratio}")
    
    # Check cache first
    if use_cache:
        cached_url = image_service.get_cached_image(prompt, level, style_hint, aspect_ratio)
        if cached_url:
            logger.info(f"Using cached image for prompt: {prompt[:50]}...")
            return cached_url
=======
def generate_and_save_image(prompt, output_filename=None, retries=2, level="moderate", style_hint=None):
    logger.debug(f"Generating image for '{prompt}' with style_hint: {style_hint}")
    
    # Check memory before starting
    initial_memory = check_memory_and_cleanup()
    logger.debug(f"Starting image generation with memory: {initial_memory:.1f} MB")
>>>>>>> 9129cfe4b41d693ce0501e8a686c17ac643b01c0
    
    if not output_filename:
        output_filename = generate_unique_image_filename(prompt, level=level, style_hint=style_hint)

<<<<<<< HEAD
    # Enhanced prompt engineering based on style, level, and aspect ratio
    def build_enhanced_prompt(base_prompt, style, reading_level, aspect_ratio=None, 
                             consistency_prompt=None, negative_prompts=None):
=======
    def build_enhanced_prompt(base_prompt, style, reading_level):
>>>>>>> 9129cfe4b41d693ce0501e8a686c17ac643b01c0
        quality_enhancers = [
            "high quality", "detailed", "vibrant colors",
            "professional illustration", "crisp and clear", "8k resolution",
            "masterpiece", "best quality", "ultra detailed"
        ]
<<<<<<< HEAD

        # Negative prompts to improve quality
        default_negative = [
            "low quality", "blurry", "distorted", "text in image", "watermark",
            "signature", "bad anatomy", "worst quality", "low resolution"
        ]
        if negative_prompts:
            default_negative.extend(negative_prompts)

=======
>>>>>>> 9129cfe4b41d693ce0501e8a686c17ac643b01c0
        style_specific = {
            "Studio Ghibli": [
                "Studio Ghibli style", "whimsical", "cinematic",
                "hand-drawn aesthetic", "soft lighting", "dreamy atmosphere",
                "Miyazaki inspired", "pastel colors", "nature-focused"
            ],
            "Educational": [
                "educational illustration", "clear and simple",
                "easy to understand", "child-friendly", "informative",
                "diagram-style", "clean lines", "well-organized"
            ],
            "Disney Classic": [
                "Disney classic animation style", "hand-drawn", "vibrant colors",
                "expressive characters", "magical atmosphere", "timeless appeal",
                "cel-shaded", "character-focused"
            ],
            "Comic Book": [
                "comic book style", "bold lines", "dynamic composition",
                "pop art colors", "action-packed", "graphic novel aesthetic",
                "halftone patterns", "comic panel style"
            ],
            "Watercolor": [
                "watercolor painting style", "soft edges", "flowing colors",
                "artistic", "ethereal", "dreamy atmosphere", "pigment texture",
                "paper texture visible"
            ],
            "Pixel Art": [
                "pixel art style", "retro gaming aesthetic", "8-bit inspired",
                "blocky", "nostalgic", "digital art", "pixel perfect",
                "limited color palette"
            ],
            "3D Render": [
                "3D rendered style", "photorealistic", "modern",
                "detailed textures", "professional lighting", "contemporary look",
                "ray-traced", "high poly count"
            ]
        }
        level_specific = {
<<<<<<< HEAD
            "Kid": ["simple", "friendly", "bright colors", "cartoon style", "innocent", "safe"],
            "PreTeen": ["engaging", "modern style", "relatable", "adventurous", "exciting"],
            "Teen": ["stylish", "contemporary", "appealing to young adults", "trendy"],
            "University": ["sophisticated", "professional", "academic style", "realistic"],
            "Standard": ["balanced", "universal appeal", "accessible"]
        }

        # Aspect ratio considerations
        aspect_ratio_hints = {
            "square": "1:1 aspect ratio, centered composition",
            "landscape": "16:9 aspect ratio, wide composition, cinematic framing",
            "portrait": "9:16 aspect ratio, vertical composition, mobile-friendly"
=======
            "beginner": ["simple", "friendly", "bright colors", "cartoon style"],
            "moderate": ["engaging", "modern style", "relatable"],
            "intermediate": ["stylish", "contemporary", "appealing to young adults"]
>>>>>>> 9129cfe4b41d693ce0501e8a686c17ac643b01c0
        }
        level_enhancers = level_specific.get(reading_level, level_specific["moderate"])
        style_enhancers = style_specific.get(style, [])
<<<<<<< HEAD
        level_enhancers = level_specific.get(reading_level, level_specific["Standard"])
        aspect_hint = aspect_ratio_hints.get(aspect_ratio, "") if aspect_ratio else ""

        all_enhancers = quality_enhancers + style_enhancers + level_enhancers
        enhanced_prompt = f"{base_prompt}. {' '.join(all_enhancers)}"
        
        if aspect_hint:
            enhanced_prompt += f". {aspect_hint}"
        
        if consistency_prompt:
            enhanced_prompt = f"{consistency_prompt} {enhanced_prompt}"
        
        enhanced_prompt += ". No text or captions in the image."

        return enhanced_prompt, default_negative
=======
        all_enhancers = quality_enhancers + style_enhancers + level_enhancers
        enhanced_prompt = f"{base_prompt}. {' '.join(all_enhancers)}. No text or captions in the image."
        return enhanced_prompt
>>>>>>> 9129cfe4b41d693ce0501e8a686c17ac643b01c0

    # Build consistency prompt if needed
    if story_id and character_name and not consistency_prompt:
        consistency_prompt = consistency_manager.build_consistency_prompt(
            prompt, story_id=story_id, character_name=character_name
        )
    elif consistency_prompt is None:
        consistency_prompt = ""
    
    # Model fallback chain
    models_to_try = [
        (PRIMARY_IMAGE_MODEL, "Gemini 3 Pro"),
        (FALLBACK_IMAGE_MODEL, "Gemini 2.5 Flash"),
        (LEGACY_IMAGE_MODEL, "Gemini 2.0 Flash (Legacy)")
    ]
    
    start_time = time.time()
    last_error = None
    
    for model_name, model_label in models_to_try:
    for attempt in range(retries):
        try:
<<<<<<< HEAD
                enhanced_prompt, negative_prompts = build_enhanced_prompt(
                    prompt, style_hint, level, aspect_ratio, consistency_prompt
                )
                logger.debug(f"Calling {model_label} with enhanced prompt: {enhanced_prompt[:200]}...")

                # Build config with aspect ratio if supported
                config_params = {
                    'response_modalities': ['TEXT', 'IMAGE'],
                    'temperature': 0.7,
                    'top_p': 0.6,
                    'top_k': 40
                }
                
                # Add aspect ratio if using Gemini 2.5 Flash Image or 3.0 Pro
                if aspect_ratio and model_name in [PRIMARY_IMAGE_MODEL, FALLBACK_IMAGE_MODEL]:
                    # Map aspect ratio to API format
                    aspect_ratio_map = {
                        "square": "1:1",
                        "landscape": "16:9",
                        "portrait": "9:16"
                    }
                    if aspect_ratio in aspect_ratio_map:
                        # Note: Actual parameter name may vary by API version
                        # This is a placeholder for aspect ratio support
                        logger.debug(f"Using aspect ratio: {aspect_ratio_map[aspect_ratio]}")

            resp = client.models.generate_content(
                    model=model_name,
                contents=[enhanced_prompt],
                    config=types.GenerateContentConfig(**config_params)
            )

                logger.debug(f"{model_label} response received (attempt {attempt+1}).")

            if not resp.candidates or not resp.candidates[0].content.parts:
                    logger.warning(f"{model_label} response had no candidates or parts for prompt: {prompt}")
                raise ValueError("No content parts in response")

            img_part = next((p for p in resp.candidates[0].content.parts
                             if p.inline_data and 'image' in p.inline_data.mime_type), None)

            if not img_part:
                    logger.warning(f"{model_label} image response did not contain image data part for prompt: {prompt}")
                text_part = next((p for p in resp.candidates[0].content.parts if p.text), None)
                if text_part:
                        logger.warning(f"{model_label} response contained text part: {text_part.text[:200]}...")
                raise ValueError("No image data part in response")

            logger.debug(f"Image part found. MIME type: {img_part.inline_data.mime_type}, Data length: {len(img_part.inline_data.data)}")

            image_data_bytes = img_part.inline_data.data
            if not isinstance(image_data_bytes, bytes):
                logger.error(f"Image data is not bytes, got type: {type(image_data_bytes)}")
                raise ValueError("Image data is not in bytes format")

            if len(image_data_bytes) < 1000:
                logger.warning(f"Image data too small ({len(image_data_bytes)} bytes) for prompt: {prompt}")
                raise ValueError("Image data too small to be a valid image")

            if len(image_data_bytes) > 8 and image_data_bytes[:4] != b'\x89PNG':
                logger.warning(f"Image data does not start with PNG header: {image_data_bytes[:8].hex()}")
                raise ValueError("Image data is not a valid PNG")

            logger.debug(f"Raw PNG data validated. First 8 bytes: {image_data_bytes[:8].hex()}")
            try:
                image = Image.open(BytesIO(image_data_bytes))
                image.verify()
                logger.debug("Pillow successfully opened and verified image data.")
                image = Image.open(BytesIO(image_data_bytes))

                # Optional: Add basic image enhancement
                if image.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1])
                    image = background

                buffer = BytesIO()
                image.save(buffer, format="PNG", optimize=True)
                buffer.seek(0)

                blob = bucket.blob(f"images/{output_filename}")
                blob.upload_from_file(buffer, content_type="image/png")
                logger.info(f"Image uploaded to GCS: {output_filename}")

                expiration_time = datetime.timedelta(minutes=60)
                signed_url = blob.generate_signed_url(
                    version="v4",
                    expiration=expiration_time,
                    method="GET"
                )
                logger.debug(f"Generated signed URL: {signed_url[:80]}...")
                    
                    # Cache the result
                    if use_cache:
                        image_service.cache_image(prompt, level, style_hint, signed_url, aspect_ratio)
                    
                    generation_time = time.time() - start_time
                    logger.info(f"Successfully generated image using {model_label} in {generation_time:.2f}s")
                    
                return signed_url

            except OSError as oe:
                    logger.error(f"Pillow failed to identify or verify image file ({model_label}, attempt {attempt+1}): {oe}")
                    last_error = oe
                    if attempt < retries - 1:
                        continue
                    # Try next model
                    break
            except Exception as e:
                    logger.error(f"Unexpected error processing image with {model_label} (attempt {attempt+1}): {e}")
                    last_error = e
                    if attempt < retries - 1:
                        continue
                    # Try next model
                    break

=======
            # Check memory before each attempt
            current_memory = check_memory_and_cleanup()
            if current_memory > MEMORY_LIMIT_MB:
                logger.error(f"Memory usage too high ({current_memory:.1f} MB) for image generation. Skipping.")
                raise MemoryError(f"Memory usage exceeds limit: {current_memory:.1f} MB")
            
            enhanced_prompt = build_enhanced_prompt(prompt, style_hint, level)
            logger.debug(f"Calling GenAI image model with enhanced prompt: {enhanced_prompt}")
            
            response = client.models.generate_content(
                model="gemini-2.0-flash-preview-image-generation",
                contents=enhanced_prompt,
                config=types.GenerateContentConfig(
                   response_modalities=['TEXT', 'IMAGE']
                )
            )
            
            # Add proper null checking for response
            if not response:
                logger.error(f"Image generation returned None response for prompt: {prompt}")
                raise ValueError("No response received from image generation model")
            
            if (not hasattr(response, 'candidates') or 
                not response.candidates or 
                len(response.candidates) == 0 or
                not hasattr(response.candidates[0], 'content') or
                not response.candidates[0].content or
                not hasattr(response.candidates[0].content, 'parts') or
                not response.candidates[0].content.parts):
                logger.error(f"Image generation response missing expected structure for prompt: {prompt}")
                raise ValueError("Image generation response missing expected structure")
            
            found_image = False
            for part in response.candidates[0].content.parts:
                if getattr(part, 'inline_data', None) is not None:
                    image_data_bytes = part.inline_data.data
                    
                    # Use safe image processing
                    buffer = safe_image_processing(image_data_bytes, prompt)
                    
                    # Upload to GCS using helper function
                    signed_url = upload_buffer_to_gcs(buffer, f"images/{output_filename}", "image/png")
                    
                    if signed_url:
                        logger.info(f"Image uploaded to GCS: {output_filename}")
                        logger.debug(f"Generated signed URL: {signed_url[:80]}...")
                        
                        # Clean up buffer
                        buffer.close()
                        del buffer
                        gc.collect()
                        
                        # Final memory check
                        final_memory = get_memory_usage()
                        logger.info(f"Image generation complete. Memory: {final_memory:.1f} MB")
                        
                        return signed_url
                    else:
                        logger.error(f"Failed to upload image to GCS: {output_filename}")
                        buffer.close()
                        del buffer
                        gc.collect()
                        raise Exception("Failed to upload image to GCS")
                
            if not found_image:
                logger.warning(f"No image data part found in response for prompt: {prompt}")
                raise ValueError("No image data part in response")
                
        except MemoryError as e:
            logger.error(f"Memory error on attempt {attempt+1}: {e}")
            gc.collect()
            time.sleep(2)  # Wait before retry
            if attempt == retries - 1:
                logger.warning(f"All attempts failed due to memory issues for prompt '{prompt}'. Falling back to placeholder.")
                return create_placeholder_image(prompt, style_hint=style_hint)
            continue
>>>>>>> 9129cfe4b41d693ce0501e8a686c17ac643b01c0
        except Exception as e:
                logger.error(f"{model_label} API call failed (attempt {attempt+1}): {e}")
                last_error = e
                if attempt < retries - 1:
            continue
<<<<<<< HEAD
                # Try next model in fallback chain
                break
    
    # All models failed, fall back to placeholder
    logger.warning(f"All image generation attempts failed for prompt '{prompt}'. Last error: {last_error}")
    logger.warning("Falling back to placeholder image.")
    placeholder_url = create_placeholder_image(prompt, style_hint=style_hint)
    return placeholder_url
=======
    
    logger.error(f"generate_and_save_image reached end without returning URL for prompt: {prompt}")
    return create_placeholder_image(prompt, style_hint=style_hint)
>>>>>>> 9129cfe4b41d693ce0501e8a686c17ac643b01c0

def generate_dyslexic_text(level_adjusted_input_text, system_instruction_override=None):
    # Use the model with system instruction set in constructor
    logger.debug(f"Generating text for input (first 100 chars): {level_adjusted_input_text[:100]}...")
    
    try:
        # If we need to override the system instruction, create a new model instance
        if system_instruction_override:
           
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=level_adjusted_input_text,
                 config=types.GenerateContentConfig(
        system_instruction=system_instruction_override),
                )
        else:
            # Use the default model with SYSTEM_INSTRUCTION
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=level_adjusted_input_text,
                 config=types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION),
                )

        # Keep the improved response validation logic
        if not resp.candidates or not hasattr(resp.candidates[0].content, 'parts') or not resp.candidates[0].content.parts:
             logger.error("Text generation response missing expected structure (candidates/parts).")
             # Adding check for prompt feedback which might indicate blocking
             if resp.prompt_feedback:
                 logger.error(f"Prompt Feedback: {resp.prompt_feedback}")
             return None
        # Extract text using .text shortcut if available and safe
        if hasattr(resp, 'text'):
            logger.info(f"Text generation successful. Content length: {len(resp.text)}")
            return resp.text
        else:
            # Fallback to checking parts manually (as in the 'levels' version)
            text_part = next((p for p in resp.candidates[0].content.parts if hasattr(p, 'text')), None)
            if not text_part:
                 logger.error("Text generation response missing text part.")
                 logger.debug(f"Full response parts: {resp.candidates[0].content.parts}")
                 if resp.prompt_feedback:
                     logger.error(f"Prompt Feedback: {resp.prompt_feedback}")
                 return None
            logger.info(f"Text generation successful (via parts). Content length: {len(text_part.text)}")
            return text_part.text

    except Exception as e:
        logger.error(f"Error during text generation: {e}")
        logger.exception("Exception details:")
        return None

def process_input_text(input_text, level="moderate", summarization_tier="Detailed Explanation", profile_context=None,
                       explain_again_mode=False, original_paragraph_text=None,
                       output_format=None,
                       dialogue_mode=False, selected_text_snippet=None, original_block_content=None, conversation_history=None, user_question=None,
                       image_style=None, request_id=None, user_token=None):  # Add user_token parameter
    # Generate request ID if not provided
    if not request_id:
        request_id = str(uuid4())
    
    # Store user token for notifications
    if user_token:
        request_user_tokens[request_id] = user_token
    
    # Store request data for persistence
    request_data[request_id] = {
        'input_text': input_text,
        'level': level,
        'summarization_tier': summarization_tier,
        'profile_context': profile_context,
        'explain_again_mode': explain_again_mode,
        'original_paragraph_text': original_paragraph_text,
        'output_format': output_format,
        'dialogue_mode': dialogue_mode,
        'selected_text_snippet': selected_text_snippet,
        'original_block_content': original_block_content,
        'conversation_history': conversation_history,
        'user_question': user_question,
        'image_style': image_style,
        'user_token': user_token,
        'created_at': datetime.now().isoformat()
    }
    
    # Initialize progress tracking
    request_progress[request_id] = {
        'step': 'Starting...',
        'step_number': 0,
        'total_steps': 10,  # Will be updated based on content type
        'details': '',
        'last_updated': datetime.now().isoformat(),
        'progress_percentage': 0
    }
    request_start_times[request_id] = datetime.now()
    
    # Update Firebase with initial task status
    update_firebase_task_status(request_id, 'started')
    
    logger.info(f"Processing input with level: {level}, summarization_tier: {summarization_tier}, profile_context: {profile_context}, explain_again: {explain_again_mode}, output_format: {output_format}, dialogue_mode: {dialogue_mode}, image_style: {image_style}, request_id: {request_id}")

    # Check if this is a story generation request
    is_story_generation = False
    genre = None
    main_character = None

    # Parse story generation parameters from input text
    if "[Level:" in input_text and "Please convert the following text into an engaging" in input_text:
        is_story_generation = True
        # Extract genre
        genre_match = re.search(r"into an engaging (\w+) story", input_text)
        if genre_match:
            genre = genre_match.group(1).capitalize()

        # Extract main character
        character_match = re.search(r"Main Character: (.*?)\n", input_text)
        if character_match:
            main_character = character_match.group(1).strip()

        # Extract original text
        original_text_match = re.search(r"Original Text:\n(.*)", input_text, re.DOTALL)
        if original_text_match:
            input_text = original_text_match.group(1).strip()

    if is_story_generation:
        # Update progress for story generation
        update_request_progress(request_id, "Preparing story generation", 1, 8, f"Genre: {genre}, Character: {main_character or 'None'}")
        
        # Prepare genre-specific instructions
        genre_guidelines = "\n".join([f"- {genre}: {description}" for genre, description in STORY_GENRES.items()])
        story_instruction = STORY_GENERATION_INSTRUCTION.format(genre_guidelines=genre_guidelines)

        # Add character context if provided
        if main_character:
            story_instruction += f"\n\nMain Character Context:\nThe story should feature {main_character} as the main character. Develop their personality and role in the story naturally."

        # Add genre-specific context
        if genre and genre in STORY_GENRES:
            story_instruction += f"\n\nGenre Context:\n{STORY_GENRES[genre]}"

        # Use story generation instruction instead of default
        system_instruction_override = story_instruction
    else:
        system_instruction_override = None

    if level not in READING_LEVELS:
        logger.warning(f"Invalid level '{level}' received. Defaulting to 'moderate'.")
        level = "moderate"

    valid_tiers = ["Detailed Explanation"]
    if not explain_again_mode and output_format is None and not dialogue_mode and summarization_tier not in valid_tiers:
        logger.warning(f"Invalid summarization_tier '{summarization_tier}'. Defaulting to 'Detailed Explanation'.")
        summarization_tier = "Detailed Explanation"

    profile_info_str_for_prompt = "Not specified"
    if profile_context:
        student_level_info = profile_context.get('studentLevel', 'Not specified')
        topics_of_interest_info = profile_context.get('topicsOfInterest', 'Not specified')
        if isinstance(topics_of_interest_info, list):
            topics_of_interest_info = ", ".join(topics_of_interest_info)
        profile_info_str_for_prompt = f"Student Level={student_level_info}, Interests={topics_of_interest_info}"

    if dialogue_mode:
        update_request_progress(request_id, "Processing dialogue", 1, 3, "Generating conversational response")
        logger.info(f"Dialogue Mode: User Question='{user_question}', Snippet='{selected_text_snippet[:100]}...', Block Context='{original_block_content[:100]}...'")
        if not user_question or not selected_text_snippet or not original_block_content:
            logger.error("Dialogue mode: Missing one or more required fields: user_question, selected_text_snippet, original_block_content.")
            cleanup_request_progress(request_id)
            update_firebase_task_status(request_id, 'failed', error_message="Missing required information for dialogue mode")
            return {"error": "Missing required information for dialogue mode."}, 400

        history_str = ""
        if conversation_history:
            for msg in conversation_history:
                sender = "User" if msg.get("sender") == "user" else "AI"
                history_str += f"{sender}: {msg.get('text')}\n"
        else:
            history_str = "No previous conversation in this session."

        dialogue_prompt_filled = DIALOGUE_PROMPT_TEMPLATE.format(
            level=level,
            profile_context_str=profile_info_str_for_prompt,
            original_block_content=original_block_content,
            selected_text_snippet=selected_text_snippet,
            conversation_history=history_str.strip(),
            user_question=user_question
        )

        update_request_progress(request_id, "Generating dialogue response", 2, 3, "Using AI model")
        dialogue_response_text = generate_dyslexic_text(dialogue_prompt_filled, system_instruction_override="You are an AI Conversational Tutor for ReadBuddy. Respond to the user's latest question based on the provided context and conversation history.")

        if not dialogue_response_text or not dialogue_response_text.strip():
            logger.error("Failed to generate dialogue response or got empty response.")
            cleanup_request_progress(request_id)
            update_firebase_task_status(request_id, 'failed', error_message="Failed to get a dialogue response")
            return {"dialogue_response": "I'm sorry, I couldn't come up with a response for that. Could you try asking in a different way?", "error": "Failed to get a dialogue response."}, 200

        update_request_progress(request_id, "Dialogue complete", 3, 3, "Response generated successfully")
        logger.info(f"Dialogue response generated: {dialogue_response_text[:100]}...")
        
        # Send completion notification
        if user_token:
            send_push_notification(
                user_token,
                "Dialogue Complete! 💬",
                "Your conversation response is ready",
                {'request_id': request_id, 'type': 'dialogue'}
            )
        
        update_firebase_task_status(request_id, 'completed', {'dialogue_response': dialogue_response_text.strip()})
        cleanup_request_progress(request_id)
        return {"dialogue_response": dialogue_response_text.strip()}, 200

    if explain_again_mode and original_paragraph_text:
        update_request_progress(request_id, "Re-explaining content", 1, 2, "Processing alternative explanation")
        logger.info(f"Explain Again Mode for paragraph: {original_paragraph_text[:100]}...")

        prompt_for_re_explanation = EXPLAIN_AGAIN_PROMPT_TEMPLATE.format(
            level=level,
            profile_context_str=profile_info_str_for_prompt,
            original_paragraph=original_paragraph_text
        )

        update_request_progress(request_id, "Generating alternative explanation", 2, 2, "Using AI model")
        re_explained_text_content = generate_dyslexic_text(prompt_for_re_explanation, system_instruction_override="You are an expert at rephrasing and clarifying text for better understanding. Follow the user's instructions precisely.")

        if not re_explained_text_content or not re_explained_text_content.strip():
            logger.error("Failed to generate re-explained content or got empty response.")
            cleanup_request_progress(request_id)
            update_firebase_task_status(request_id, 'failed', error_message="Failed to get a new explanation")
            return {"re_explained_paragraph": original_paragraph_text, "error": "Failed to get a new explanation."}, 200

        logger.info(f"Re-explained content generated: {re_explained_text_content[:100]}...")
        
        # Send completion notification
        if user_token:
            send_push_notification(
                user_token,
                "Explanation Ready! 📝",
                "Your alternative explanation is complete",
                {'request_id': request_id, 'type': 'explain_again'}
            )
        
        update_firebase_task_status(request_id, 'completed', {'re_explained_paragraph': re_explained_text_content.strip()})
        cleanup_request_progress(request_id)
        return {"re_explained_paragraph": re_explained_text_content.strip()}, 200

    if output_format == "flashcards":
        update_request_progress(request_id, "Generating flashcards", 1, 3, "Extracting key concepts")
        logger.info(f"Flashcard Generation Mode for text: {input_text[:100]}...")
        flashcard_prompt = FLASHCARD_PROMPT_TEMPLATE.format(
            level=level,
            profile_context_str=profile_info_str_for_prompt,
            input_text=input_text
        )
        update_request_progress(request_id, "Creating flashcard content", 2, 3, "Using AI model")
        flashcard_json_string = generate_dyslexic_text(flashcard_prompt, system_instruction_override="Generate flashcards based on the input text and context. Output **only** the JSON array as specified.")
        if not flashcard_json_string or not flashcard_json_string.strip():
            logger.error("Failed to generate flashcard content or got empty response.")
            cleanup_request_progress(request_id)
            update_firebase_task_status(request_id, 'failed', error_message="Failed to generate flashcards")
            return {"error": "Failed to generate flashcards."}, 500
        try:
            update_request_progress(request_id, "Processing flashcard data", 3, 3, "Validating JSON format")
            cleaned_json = clean_json_string(flashcard_json_string)
            flashcards_data = json.loads(cleaned_json)
            if not isinstance(flashcards_data, list):
                raise ValueError("Generated flashcards are not a JSON array.")
            for item in flashcards_data:
                if not isinstance(item, dict) or "front" not in item or "back" not in item:
                    raise ValueError("Invalid flashcard item structure.")
            if not flashcards_data:
                logger.warning("AI returned empty flashcard array. Adding fallback card.")
                flashcards_data = [{"front": "No content", "back": "No flashcards could be generated for this topic."}]
            logger.info(f"Successfully generated and parsed {len(flashcards_data)} flashcards.")
            
            # Send completion notification
            if user_token:
                send_push_notification(
                    user_token,
                    "Flashcards Ready! 🗂️",
                    f"Generated {len(flashcards_data)} flashcards for you",
                    {'request_id': request_id, 'type': 'flashcards', 'count': str(len(flashcards_data))}
                )
            
            update_firebase_task_status(request_id, 'completed', {'flashcards': flashcards_data})
            cleanup_request_progress(request_id)
            return {"flashcards": flashcards_data}, 200
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode generated flashcards JSON: {e}. String was: {cleaned_json[:500]}...")
            cleanup_request_progress(request_id)
            update_firebase_task_status(request_id, 'failed', error_message="Failed to parse generated flashcards format")
            return {"error": "Failed to parse generated flashcards format."}, 500
        except ValueError as e:
            logger.error(f"Generated flashcards validation error: {e}. String was: {cleaned_json[:500]}...")
            cleanup_request_progress(request_id)
            update_firebase_task_status(request_id, 'failed', error_message=f"Generated flashcards had unexpected structure: {e}")
            return {"error": f"Generated flashcards had unexpected structure: {e}"}, 500

    if output_format == "slideshow":
        update_request_progress(request_id, "Generating slideshow", 1, 3, "Breaking down content")
        logger.info(f"Slideshow Generation Mode for text: {input_text[:100]}...")
        slideshow_prompt = SLIDESHOW_PROMPT_TEMPLATE.format(
            level=level,
            profile_context_str=profile_info_str_for_prompt,
            input_text=input_text
        )
        update_request_progress(request_id, "Creating slide content", 2, 3, "Using AI model")
        slideshow_json_string = generate_dyslexic_text(slideshow_prompt, system_instruction_override="Generate a slideshow based on the input text and context. Output **only** the JSON array as specified.")
        slideshow_data = process_json_response(slideshow_json_string, "array")

        # Validate slideshow structure
        if not slideshow_data:
            logger.warning("AI returned empty slideshow array. Adding fallback slide.")
            slideshow_data = [{"content": ["No content provided."]}]
        else:
            for item in slideshow_data:
                if not isinstance(item, dict) or "content" not in item or not isinstance(item["content"], list):
                    raise ValueError("Invalid slide item structure (missing 'content' array)")
                if "title" in item and not isinstance(item["title"], (str, type(None))):
                    raise ValueError("Invalid slide item structure ('title' must be string or null)")

        update_request_progress(request_id, "Slideshow complete", 3, 3, f"Generated {len(slideshow_data)} slides")
        logger.info(f"Successfully generated and parsed {len(slideshow_data)} slides.")
        
        # Send completion notification
        if user_token:
            send_push_notification(
                user_token,
                "Slideshow Ready! 📊",
                f"Created {len(slideshow_data)} slides for you",
                {'request_id': request_id, 'type': 'slideshow', 'count': str(len(slideshow_data))}
            )
        
        update_firebase_task_status(request_id, 'completed', {'slides': slideshow_data})
        cleanup_request_progress(request_id)
        return {"slides": slideshow_data}, 200

    # Default content generation with detailed progress tracking
    update_request_progress(request_id, "Preparing content generation", 1, 8, f"Level: {level}, Type: {summarization_tier}")
    logger.info("Default content block generation mode selected.")
    level_adjusted_input = f"[Level: {level}] [Summary Tier: {summarization_tier}] [Profile: {profile_info_str_for_prompt}]\n\n{input_text}"
    logger.debug(f"Constructed level_adjusted_input for full generation: {level_adjusted_input[:200]}...")

    update_request_progress(request_id, "Generating text content", 2, 8, "Using AI model")
    text_content = generate_dyslexic_text(level_adjusted_input)
    if not text_content:
        logger.error("Failed to generate text content.")
        cleanup_request_progress(request_id)
        update_firebase_task_status(request_id, 'failed', error_message="Failed to generate educational content")
        return {"error": "Failed to generate educational content. Please try again later."}, 500

    update_request_progress(request_id, "Parsing content blocks", 3, 8, "Extracting structure")
    logger.debug(f"Generated text received for block parsing. Summarization Tier: {summarization_tier}. Proceeding with parsing.")
    blocks = []

    logger.debug("Detailed Explanation tier. Proceeding with image extraction and full block parsing.")
    current_text_to_process = text_content
    ghibli_image_match = re.search(r'\[GhibliImage:\s*(.*?)\s*\]\n?', current_text_to_process, re.IGNORECASE)
    if ghibli_image_match:
        update_request_progress(request_id, "Generating summary image", 4, 8, "Creating Ghibli-style illustration")
        ghibli_prompt = ghibli_image_match.group(1).strip()
        logger.info(f"Found GhibliImage prompt: '{ghibli_prompt}'")
        ghibli_filename = generate_unique_image_filename(ghibli_prompt, level=level, style_hint=image_style, prefix="ghibli_summary")
        ghibli_signed_url = generate_and_save_image(ghibli_prompt, ghibli_filename, level=level, style_hint=image_style)
        if ghibli_signed_url:
            blocks.append({
                "type": "image",
                "url": ghibli_signed_url,
                "alt": f"Summary illustration: {ghibli_prompt}",
                "id": str(uuid4())
            })
            logger.debug(f"Added GhibliImage block: {ghibli_prompt[:50]}...")
        else:
            logger.error(f"Failed to generate or get URL for GhibliImage prompt: {ghibli_prompt}")
            blocks.append({
                "type": "error",
                "content": f"Failed to generate summary image for: {ghibli_prompt[:50]}...",
                "id": str(uuid4())
            })
        current_text_to_process = current_text_to_process.replace(ghibli_image_match.group(0), "", 1)
    else:
        logger.warning("No GhibliImage prompt found at the beginning of the Detailed Explanation content.")
    
    update_request_progress(request_id, "Processing content blocks", 5, 8, "Extracting text and images")
    image_placeholders = []
    for match in re.finditer(r'\[Image:\s*(.*?)\s*\]', current_text_to_process, re.IGNORECASE):
        image_placeholders.append({'type': 'image', 'prompt': match.group(1).strip(), 'match_obj': match})
    all_placeholders = sorted(image_placeholders, key=lambda p: p['match_obj'].start())
    last_idx = 0
    processed_text_parts = []
    for placeholder in all_placeholders:
        match_obj = placeholder['match_obj']
        if match_obj.start() > last_idx:
            processed_text_parts.append({'type': 'text_segment', 'content': current_text_to_process[last_idx:match_obj.start()]})
        processed_text_parts.append(placeholder)
        last_idx = match_obj.end()
    if last_idx < len(current_text_to_process):
        processed_text_parts.append({'type': 'text_segment', 'content': current_text_to_process[last_idx:]})
    
    update_request_progress(request_id, "Generating content images", 6, 8, f"Processing {len(image_placeholders)} images")
    image_idx_counter = 0
    for part in processed_text_parts:
        if part['type'] == 'text_segment':
            segment_content = part['content']
            lines = segment_content.split('\n')
            quiz_heading_pattern = re.compile(r"^\*\*(Quiz Time!|Test Your Knowledge!?)\*\*", re.IGNORECASE)
            question_start_pattern = re.compile(r"^\d+\.\s*(.+)$")
            option_pattern = re.compile(r"^([a-z])\)\s*(.+)$", re.IGNORECASE)
            correct_answer_pattern = re.compile(r"^Correct Answer:\s*([a-z])$", re.IGNORECASE)
            explanation_pattern = re.compile(r"^Explanation:\s*(.+)$", re.IGNORECASE)
            heading_pattern = re.compile(r"^\*\*(?!(?:Quiz Time!|Test Your Knowledge!?)$)(.+?)\*\*$")
            current_paragraph_lines = []
            def flush_paragraph_segment(lines_list, block_list_target):
                if lines_list:
                    content = "\n".join(lines_list).strip()
                    if content:
                        block_list_target.append({"type": "paragraph", "content": content, "id": str(uuid4())})
                        logger.debug(f"Added Paragraph block (from segment): {content[:50]}...")
                    lines_list.clear()
            line_idx_segment = 0
            while line_idx_segment < len(lines):
                line = lines[line_idx_segment].strip()
                if not line:
                    flush_paragraph_segment(current_paragraph_lines, blocks)
                    line_idx_segment += 1
                    continue
                quiz_head_match = quiz_heading_pattern.match(line)
                if quiz_head_match:
                    flush_paragraph_segment(current_paragraph_lines, blocks)
                    quiz_title = line.strip('*!? ')
                    blocks.append({"type": "quizHeading", "content": quiz_title, "id": str(uuid4())})
                    logger.debug(f"Added Quiz Heading block (from segment): {quiz_title}")
                    line_idx_segment += 1
                    continue
                q_start_match = question_start_pattern.match(line)
                if q_start_match:
                    flush_paragraph_segment(current_paragraph_lines, blocks)
                    question_text = q_start_match.group(1).strip()
                    parsed_options = []
                    parsed_correct_answer_id = None
                    parsed_explanation = None
                    option_id_map = {}
                    temp_line_idx = line_idx_segment + 1
                    while temp_line_idx < len(lines):
                        opt_line = lines[temp_line_idx].strip()
                        if not opt_line:
                            temp_line_idx +=1
                            continue
                        opt_match = option_pattern.match(opt_line)
                        if opt_match:
                            opt_char = opt_match.group(1).lower()
                            opt_text = opt_match.group(2).strip()
                            full_opt_id = f"opt-{opt_char}-{uuid4().hex[:6]}"
                            parsed_options.append({"id": full_opt_id, "text": opt_text})
                            option_id_map[opt_char] = full_opt_id
                            temp_line_idx += 1
                        else:
                            break
                    if temp_line_idx < len(lines):
                        corr_ans_line = lines[temp_line_idx].strip()
                        if not corr_ans_line and temp_line_idx + 1 < len(lines):
                            temp_line_idx += 1
                            corr_ans_line = lines[temp_line_idx].strip()
                        corr_ans_match = correct_answer_pattern.match(corr_ans_line)
                        if corr_ans_match:
                            corr_char = corr_ans_match.group(1).lower()
                            if corr_char in option_id_map:
                                parsed_correct_answer_id = option_id_map[corr_char]
                            temp_line_idx += 1
                    if temp_line_idx < len(lines):
                        expl_line = lines[temp_line_idx].strip()
                        if not expl_line and temp_line_idx + 1 < len(lines):
                            temp_line_idx += 1
                            expl_line = lines[temp_line_idx].strip()
                        expl_match = explanation_pattern.match(expl_line)
                        if expl_match:
                            parsed_explanation = expl_match.group(1).strip()
                            temp_line_idx += 1
                    if question_text and parsed_options and parsed_correct_answer_id:
                        blocks.append({
                            "type": "multipleChoiceQuestion", "content": question_text,
                            "options": parsed_options, "correctAnswerID": parsed_correct_answer_id,
                            "explanation": parsed_explanation, "id": str(uuid4())
                        })
                        logger.debug(f"Added MCQ block (from segment): {question_text[:50]}...")
                        line_idx_segment = temp_line_idx
                        continue
                    else:
                        current_paragraph_lines.append(line)
                        line_idx_segment += 1
                        continue
                head_match = heading_pattern.match(line)
                if head_match:
                    flush_paragraph_segment(current_paragraph_lines, blocks)
                    heading_content = head_match.group(1).strip()
                    blocks.append({"type": "heading", "content": heading_content, "id": str(uuid4())})
                    logger.debug(f"Added Heading block (from segment): {heading_content[:50]}...")
                    line_idx_segment += 1
                    continue
                current_paragraph_lines.append(line)
                line_idx_segment += 1
            flush_paragraph_segment(current_paragraph_lines, blocks)
        elif part['type'] == 'image':
            image_idx_counter += 1
            update_request_progress(request_id, f"Generating image {image_idx_counter}", 6, 8, f"Processing image {image_idx_counter}/{len(image_placeholders)}")
            prompt = part['prompt']
            filename = generate_unique_image_filename(prompt, level=level, style_hint=image_style, prefix="image")
            logger.debug(f"Requesting regular image {image_idx_counter} for prompt: '{prompt}' -> filename: {filename}")
            signed_url = generate_and_save_image(prompt, filename, level=level, style_hint=image_style)
            if signed_url:
                blocks.append({"type": "image", "url": signed_url, "alt": prompt, "id": str(uuid4())})
                logger.debug(f"Added Image block (from placeholder): {prompt[:50]}...")
            else:
                logger.error(f"Failed to generate or get URL for regular image prompt: {prompt}")
                blocks.append({"type": "error", "content": f"Failed to generate image for: {prompt[:50]}...", "id": str(uuid4())})
    
    update_request_progress(request_id, "Finalizing content", 7, 8, "Preparing final blocks")
    logger.debug("Placeholder processing (images) complete for Detailed Explanation.")
    final_blocks = [b for b in blocks if b.get("content") or b.get("type") == "image"]
    is_only_ghibli_related = len(final_blocks) == 1 and final_blocks[0].get("type") in ["image", "error"] and ("ghibli_summary" in final_blocks[0].get("url","") or "summary image" in final_blocks[0].get("alt","") or "summary image" in final_blocks[0].get("content",""))
    if not final_blocks or (is_only_ghibli_related and not text_content.strip()):
         logger.warning("No main content blocks were parsed for Detailed Explanation (beyond Ghibli image). Adding entire original content as a single paragraph if available.")
         original_content_without_ghibli_tag = text_content
         if ghibli_image_match:
             original_content_without_ghibli_tag = text_content.replace(ghibli_image_match.group(0), "", 1).strip()
         if original_content_without_ghibli_tag:
             if not final_blocks or is_only_ghibli_related:
                 final_blocks.append({"type": "paragraph", "content": original_content_without_ghibli_tag, "id": str(uuid4())})
         elif not final_blocks :
              final_blocks.append({"type": "error", "content": "Failed to parse content into a readable format. The AI response might be empty or unparsable.", "id": str(uuid4())})
    
    update_request_progress(request_id, "Content generation complete", 8, 8, f"Generated {len(final_blocks)} blocks")
    logger.info(f"Successfully parsed into {len(final_blocks)} blocks for Detailed Explanation.")
    if not final_blocks :
        logger.warning("Parsing for Detailed Explanation resulted in zero blocks. This might indicate an issue with AI response or parsing logic.")
        cleanup_request_progress(request_id)
        update_firebase_task_status(request_id, 'failed', error_message="Failed to parse content into a readable format")
        return {"blocks": [{"type": "error", "content": "Failed to parse content into a readable format. The AI response might be empty or unparsable.", "id": str(uuid4())}]}, 200
    
    # Send completion notification
    if user_token:
        send_push_notification(
            user_token,
            "Content Ready! 📚",
            f"Generated {len(final_blocks)} content blocks for you",
            {'request_id': request_id, 'type': 'content', 'block_count': str(len(final_blocks))}
        )
    
    update_firebase_task_status(request_id, 'completed', {'blocks': final_blocks})
    cleanup_request_progress(request_id)
    return {"blocks": final_blocks, "request_id": request_id}, 200

@app.route('/process', methods=['POST'])
def process():
    if not request.is_json:
         logger.warning("Request received is not JSON.")
         return jsonify({"error": "Request must be JSON"}), 415

    data = request.json
    text_from_input = data.get('input_text', '')
    level = data.get('level', 'moderate')
    summarization_tier = data.get('summarization_tier', 'Detailed Explanation')
    profile_context = data.get('profile', {})
    explain_again_mode = data.get('explain_again_mode', False)
    original_paragraph_text_from_request = data.get('original_paragraph_text', None)
    output_format = data.get('output_format', None)
    image_style = data.get('image_style', None)  # Add image_style parameter
    user_token = data.get('user_token', None)  # Add user_token parameter

    # Parameters for Dialogue Mode
    dialogue_mode = data.get('dialogue_mode', False)
    selected_text_snippet = data.get('selected_text_snippet', None)
    original_block_content = data.get('original_block_content', None)
    conversation_history = data.get('conversation_history', None)
    user_question = data.get('user_question', None)

    # Generate request ID for progress tracking
    request_id = str(uuid4())

    if not isinstance(level, str) or level not in READING_LEVELS:
         logger.warning(f"Invalid or missing level in request: '{level}'. Defaulting to moderate.")
         level = "moderate"

    valid_tiers = ["Detailed Explanation"]
    if not explain_again_mode and output_format is None and not dialogue_mode and (not isinstance(summarization_tier, str) or summarization_tier not in valid_tiers):
        logger.warning(f"Invalid or missing summarization_tier in request: '{summarization_tier}'. Defaulting to Detailed Explanation.")
        summarization_tier = "Detailed Explanation"

    current_input_text_for_processing = ""

    if dialogue_mode:
        logger.info(f"Received Dialogue request: level='{level}', profile='{profile_context}', user_question='{user_question}', request_id='{request_id}'")
        if not user_question or not selected_text_snippet or not original_block_content:
            logger.warning("Dialogue mode: Missing one or more required fields: user_question, selected_text_snippet, original_block_content.")
            return jsonify({"error": "Missing required information for dialogue mode."}), 400
    elif explain_again_mode:
        logger.info(f"Received Explain Again request: level='{level}', profile='{profile_context}', original_paragraph_length={len(original_paragraph_text_from_request) if original_paragraph_text_from_request else 0}, request_id='{request_id}'")
        if not original_paragraph_text_from_request:
            logger.warning("Explain again mode: Request received with no original_paragraph_text.")
            return jsonify({"error": "No original paragraph provided for re-explanation"}), 400
        current_input_text_for_processing = original_paragraph_text_from_request
    elif output_format == "flashcards" or output_format == "slideshow":
        logger.info(f"Received {output_format} Generation request: level='{level}', profile='{profile_context}', input_text length={len(text_from_input)}, request_id='{request_id}'")
        if not text_from_input:
             logger.warning(f"{output_format} mode: Request received with no input_text.")
             return jsonify({"error": f"No input text provided for {output_format} generation"}), 400
        current_input_text_for_processing = text_from_input
    else:
        logger.info(f"Received Block Generation request: level='{level}', summarization_tier='{summarization_tier}', profile='{profile_context}', input_text length={len(text_from_input)}, request_id='{request_id}'")
        if not text_from_input and len(text_from_input) == 0:
           logger.warning("Block mode: Request received with no input_text.")
           return jsonify({"error": "No input text provided"}), 400
        current_input_text_for_processing = text_from_input

    result, status_code = process_input_text(
        input_text=current_input_text_for_processing,
        level=level,
        summarization_tier=summarization_tier,
        profile_context=profile_context,
        explain_again_mode=explain_again_mode,
        original_paragraph_text=original_paragraph_text_from_request,
        output_format=output_format,
        dialogue_mode=dialogue_mode,
        selected_text_snippet=selected_text_snippet,
        original_block_content=original_block_content,
        conversation_history=conversation_history,
        user_question=user_question,
        image_style=image_style,  # NEW image_style parameter
        request_id=request_id,  # NEW request_id parameter
        user_token=user_token  # NEW user_token parameter
    )
    
    # Add request_id to the response if not already present
    if isinstance(result, dict) and "request_id" not in result:
        result["request_id"] = request_id
    
    return jsonify(result), status_code

@app.route('/test-api', methods=['GET'])
def test_api():
    logger.info("Test API endpoint hit successfully.")
    return jsonify({"message": "Backend is running and supports reading levels!"}), 200

@app.route('/generate_story', methods=['POST'])
def generate_story_endpoint():
    """Endpoint to generate a story from input text, and also generate images for each chapter."""
    try:
        data = request.get_json()
        full_input_text_from_request = data.get('text', '')
<<<<<<< HEAD
        level_from_payload = data.get('level', 'Standard')
        image_style = data.get('image_style', None)
        consistency_mode = data.get('consistency_mode', False)  # Enable character consistency
        aspect_ratio = data.get('aspect_ratio', None)  # Support aspect ratios
=======
        level_from_payload = data.get('level', 'moderate')
        image_style = data.get('image_style', None)  # Add image_style parameter
>>>>>>> 9129cfe4b41d693ce0501e8a686c17ac643b01c0

        # Generate request ID for progress tracking
        request_id = str(uuid4())
        
        # Initialize progress tracking
        request_progress[request_id] = {
            'step': 'Starting story generation...',
            'step_number': 0,
            'total_steps': 6,  # Story generation + image generation per chapter
            'details': '',
            'last_updated': datetime.now().isoformat(),
            'progress_percentage': 0
        }
        request_start_times[request_id] = datetime.now()

        main_character_for_image = None
        text_for_story_model = full_input_text_from_request

        char_match = re.search(r"Main Character:\s*(.*?)(?:\n|$)", full_input_text_from_request)
        if char_match:
            main_character_for_image = char_match.group(1).strip()
            if main_character_for_image: # Ensure non-empty name
                logger.info(f"Parsed main character for image prompt: {main_character_for_image}")
            else:
                main_character_for_image = None # Treat empty name as no character
                logger.info("Main character name was empty after parsing.")

        original_text_marker_match = re.search(r"Original Text:\n(.*)", full_input_text_from_request, re.DOTALL)
        if original_text_marker_match:
            text_for_story_model = original_text_marker_match.group(1).strip()
            logger.info("Using text after 'Original Text:' marker for story generation.")
        elif main_character_for_image:
            character_line_pattern = rf"Main Character:\s*{re.escape(main_character_for_image)}\s*\n(.*)"
            match_after_char_line = re.search(character_line_pattern, full_input_text_from_request, re.DOTALL)

            if match_after_char_line:
                potential_text = match_after_char_line.group(1).strip()
                if potential_text:
                    text_for_story_model = potential_text
                    logger.info("Using text after 'Main Character:' line for story generation.")
                else:
                    logger.warning(f"Found 'Main Character: {main_character_for_image}' but no subsequent text for story. Story content will be empty.")
                    text_for_story_model = ""
            else:
                logger.warning(f"Found 'Main Character: {main_character_for_image}' but couldn't isolate subsequent story text clearly (e.g. no newline or text after character line).")
                if full_input_text_from_request.strip() == f"Main Character: {main_character_for_image}" or \
                   (full_input_text_from_request.strip().startswith("[Level:") and f"Main Character: {main_character_for_image}" in full_input_text_from_request.strip() and len(full_input_text_from_request.split(f"Main Character: {main_character_for_image}",1)[1].strip()) == 0 ) : # if it's just the command
                    text_for_story_model = ""
                    logger.info("Input seems to be just a command with character name, setting story text to empty.")

        if not text_for_story_model.strip():
            logger.error(f"No usable text found for story generation. Original input: '{full_input_text_from_request[:100]}...'")
            cleanup_request_progress(request_id)
            return jsonify({"error": "No text content provided for story generation after parsing input."}), 400

        update_request_progress(request_id, "Generating story content", 1, 6, f"Level: {level_from_payload}")
        logger.debug(f"Text for story model (first 50 chars): '{text_for_story_model[:50]}', Level: {level_from_payload}")
        story = generate_story(text_for_story_model, level_from_payload)

        if not story or not story.get('chapters'):
            logger.error("Story generation failed or returned no chapters.")
            cleanup_request_progress(request_id)
            return jsonify({"error": "Failed to generate story chapters."}), 500

        for chapter in story.get('chapters', []):
            if 'id' not in chapter or not chapter['id']:
                chapter['id'] = str(uuid.uuid4())

<<<<<<< HEAD
        # Register story and character for consistency if consistency_mode is enabled
        story_id = story.get('id', str(uuid.uuid4()))
        if consistency_mode and main_character_for_image:
            character_description = f"The main character {main_character_for_image} in {image_style or 'the story'} style"
            consistency_manager.register_character(story_id, main_character_for_image, character_description)

=======
        update_request_progress(request_id, "Generating chapter images", 2, 6, f"Processing {len(story.get('chapters', []))} chapters")
>>>>>>> 9129cfe4b41d693ce0501e8a686c17ac643b01c0
        for idx, chapter in enumerate(story.get('chapters', [])):
            chapter_summary = f"{chapter.get('title', '')}: {chapter.get('content', '')[:200]}..."

            style_description = image_style if image_style else "beautiful"
            image_prompt_base = f"Create a {style_description} illustration for this story chapter: {chapter_summary}. The image should capture the essence of the chapter. No text or captions, only art."

            if main_character_for_image:
                prompt = f"Featuring the main character, {main_character_for_image}. {image_prompt_base}"
                logger.info(f"Image prompt for chapter {idx} (with character '{main_character_for_image}'): '{prompt[:150]}...'")
            else:
                prompt = image_prompt_base
                logger.info(f"Image prompt for chapter {idx} (no character specified in input): '{prompt[:150]}...'")

            update_request_progress(request_id, f"Generating image for chapter {idx + 1}", 3 + idx, 6, f"Chapter: {chapter.get('title', '')}")

            filename = generate_unique_image_filename(
                prompt,
                level=level_from_payload,
                style_hint=image_style,
                prefix=f"story_{story_id}_chapter_{idx}"
            )

            # Use enhanced image generation with consistency support
            url = generate_and_save_image(
                prompt,
                output_filename=filename,
                retries=3,
                level=level_from_payload,
                style_hint=image_style,
                aspect_ratio=aspect_ratio,
                story_id=story_id if consistency_mode else None,
                character_name=main_character_for_image if consistency_mode else None,
                use_cache=True
            )

            if url:
                chapter['imageUrl'] = url
                # Register first chapter image as character reference if consistency mode
                if consistency_mode and main_character_for_image and idx == 0:
                    consistency_manager.register_character(story_id, main_character_for_image, 
                                                         prompt, url)
            else:
                logger.warning(f"Failed to generate image for chapter {idx}, using placeholder.")
                chapter['imageUrl'] = create_placeholder_image(
                    f"Story chapter: {chapter.get('title', '')}. Main Character: {main_character_for_image or 'Not specified'}",
                    style_hint=image_style
                )

        update_request_progress(request_id, "Story generation complete", 6, 6, f"Generated story with {len(story.get('chapters', []))} chapters")
        if 'images' in story:
            del story['images']
        
<<<<<<< HEAD
        # Return consistency references if consistency mode was used
        response_data = {"story": story}
        if consistency_mode and main_character_for_image:
            char_ref = consistency_manager.get_character_reference(story_id, main_character_for_image)
            if char_ref:
                response_data["consistency_references"] = {
                    "story_id": story_id,
                    "character_name": main_character_for_image,
                    "character_description": char_ref.get("description"),
                    "reference_url": char_ref.get("reference_url")
                }
        
        return jsonify(response_data)
=======
        cleanup_request_progress(request_id)
        return jsonify({"story": story, "request_id": request_id})
>>>>>>> 9129cfe4b41d693ce0501e8a686c17ac643b01c0
    except Exception as e:
        logger.error(f"Error in generate_story_endpoint: {str(e)}")
        if 'request_id' in locals():
            cleanup_request_progress(request_id)
        return jsonify({"error": str(e)}), 500

def generate_story(input_text, level="moderate"):
    """Generate a story based on the input text and reading level."""
    story_system_instruction = f"""You are a creative storyteller who adapts content into engaging stories for different reading levels.
    Transform the given text into a story with 2-3 chapters, following these guidelines:

    Reading Level: {level} - {READING_LEVELS[level]}

    Story Structure:
    1. Create a compelling title
    2. Divide into 2-3 chapters (not more)
    3. Each chapter: clear title, engaging content, appropriate length
    4. Use language suitable for {level} level

    Format as JSON object ONLY:
    {{
        "title": "Story Title",
        "content": "Brief story overview",
        "level": "{level}",
        "chapters": [
            {{
                "title": "Chapter 1 Title",
                "content": "Chapter 1 content",
                "order": 1
            }},
            {{
                "title": "Chapter 2 Title", 
                "content": "Chapter 2 content",
                "order": 2
            }}
        ]
    }}

    Respond with ONLY the JSON object. No explanations or markdown."""

    try:
        # Generate the story using the AI model
        response = generate_dyslexic_text(input_text, story_system_instruction)
        logger.info(f"Raw AI response for story: {str(response)[:1000]}")

        # === FIX: Check for None response ===
        if not response:
            logger.error("AI did not return a response for story generation.")
            raise ValueError("Sorry, we couldn't generate a story. Please try again or rephrase your topic.")

        # Extract JSON from response, even if wrapped in markdown or extra text
        def extract_json_from_response(resp):
            if not resp:
                return None
            # Try to find a JSON code block
            match = re.search(r"```json\\s*(\{.*?\})\\s*```", resp, re.DOTALL)
            if match:
                return match.group(1)
            # Try to find any JSON object in the text
            match = re.search(r"(\{.*\})", resp, re.DOTALL)
            if match:
                return match.group(1)
            return resp  # fallback

        def fix_truncated_json(json_str):
            """Attempt to fix truncated JSON by completing missing closing braces/brackets"""
            if not json_str:
                return json_str
            
            # Count opening and closing braces/brackets
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            open_brackets = json_str.count('[')
            close_brackets = json_str.count(']')
            
            # Add missing closing braces/brackets
            fixed_json = json_str
            for _ in range(open_braces - close_braces):
                fixed_json += '}'
            for _ in range(open_brackets - close_brackets):
                fixed_json += ']'
            
            return fixed_json

        raw_json = extract_json_from_response(response)
        
        # Try to fix truncated JSON
        fixed_json = fix_truncated_json(raw_json)
        
        try:
            story_data = json.loads(fixed_json)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse story JSON after fixing. Error: {e}. Raw: {raw_json[:1000]}")
            logger.error(f"Fixed JSON: {fixed_json[:1000]}")
            
            # Try to extract partial story data if possible
            try:
                # Look for title and content even in truncated JSON
                title_match = re.search(r'"title":\s*"([^"]*)"', raw_json)
                content_match = re.search(r'"content":\s*"([^"]*)"', raw_json)
                level_match = re.search(r'"level":\s*"([^"]*)"', raw_json)
                
                if title_match and content_match:
                    # Create a minimal valid story structure
                    story_data = {
                        "title": title_match.group(1),
                        "content": content_match.group(1),
                        "level": level_match.group(1) if level_match else level,
                        "chapters": [
                            {
                                "title": "Chapter 1",
                                "content": content_match.group(1),
                                "order": 1
                            },
                            {
                                "title": "Chapter 2",
                                "content": content_match.group(1),
                                "order": 2
                            }
                        ]
                    }
                    logger.info("Created fallback story structure from partial JSON")
                else:
                    raise ValueError("Could not extract even basic story information from truncated response")
            except Exception as fallback_error:
                logger.error(f"Fallback parsing also failed: {fallback_error}")
                raise ValueError("The AI did not return a valid story in JSON format. Please try again or rephrase your input.")

        # Validate the story structure
        if not all(key in story_data for key in ["title", "content", "level", "chapters"]):
            raise ValueError("Invalid story structure in AI response")
        for chapter in story_data["chapters"]:
            if not all(key in chapter for key in ["title", "content", "order"]):
                raise ValueError("Invalid chapter structure in AI response")
        return story_data
    except Exception as e:
        logger.error(f"Error generating story: {str(e)}")
        # Return a user-friendly error
        raise ValueError("Sorry, we couldn't generate a story. Please try again or rephrase your topic.")

def clean_json_string(s):
    """Clean and validate JSON string from AI model response.
    It should:
    - remove any lines that are not valid JSON (e.g., explanations, stray text).
    - remove any markdown code block markers.
    - remove any trailing commas before ] or }.
    - remove any leading commas.
    - ensure newlines are properly escaped.
    - escape unescaped quotes.
    - fix double-escaped quotes.

    Args:
        s (str): Raw JSON string from AI model
    Returns:
        str: Cleaned JSON string
    """
    if not s:
        return "[]"

    # Remove any markdown code block markers
    s = re.sub(r'```json\s*|\s*```', '', s)

    # Find the first [ and last ] to extract just the array
    start = s.find('[')
    end = s.rfind(']')
    if start == -1 or end == -1 or end < start:
        return "[]"
    s = s[start:end + 1]

    # Clean up common JSON formatting issues
    s = re.sub(r',\s*([\]}])', r'\1', s)  # Remove trailing commas
    s = re.sub(r'([{\[])\s*,\s*', r'\1', s)  # Remove leading commas
    s = re.sub(r'\\n', r'\\n', s)  # Ensure newlines are properly escaped
    s = re.sub(r'(?<!\\)"', r'\"', s)  # Escape unescaped quotes
    s = re.sub(r'\\"', r'\"', s)  # Fix double-escaped quotes

    return s

def process_json_response(response_string, expected_type="array"):
    """Process and validate JSON response from AI model.
    Args:
        response_string (str): Raw response string from AI model
        expected_type (str): Expected JSON type ("array" or "object")
    Returns:
        dict/list: Parsed and validated JSON data
    """
    if not response_string or not response_string.strip():
        return [] if expected_type == "array" else {}

    cleaned_json = clean_json_string(response_string)
    try:
        data = json.loads(cleaned_json)
        if expected_type == "array" and not isinstance(data, list):
            raise ValueError(f"Expected JSON array, got {type(data)}")
        elif expected_type == "object" and not isinstance(data, dict):
            raise ValueError(f"Expected JSON object, got {type(data)}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}. String was: {cleaned_json[:500]}...")
        return [] if expected_type == "array" else {}
    except ValueError as e:
        logger.error(f"JSON validation error: {e}. String was: {cleaned_json[:500]}...")
        return [] if expected_type == "array" else {}

def is_safe_prompt(prompt, level):
    blocked_terms = [
        "violence", "gore", "explicit", "nude", "naked", "blood", "weapon",
        "drug", "alcohol", "tobacco", "gambling", "hate", "discrimination"
    ]

    prompt_lower = prompt.lower()
    for term in blocked_terms:
        if term in prompt_lower:
            return False

    if level == "beginner":
        if any(word in prompt_lower for word in ["scary", "frightening", "horror"]):
            return False

    return True

@app.route('/generate_image', methods=['POST'])
def generate_image_endpoint():
    """Legacy endpoint - maintained for backwards compatibility."""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        context = data.get('context', None)
        level = data.get('level', 'moderate')
        image_style = data.get('image_style', None)

        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400
        style_hint = image_style
        if not style_hint and context == 'story_chapter':
            style_hint = 'Studio Ghibli'  # Default
        if not is_safe_prompt(prompt, level):
            return jsonify({"error": "Prompt contains inappropriate content"}), 400

        filename = generate_unique_image_filename(prompt, level=level, style_hint=style_hint, prefix="storyimg")
        signed_url = generate_and_save_image(prompt, filename, level=level, style_hint=style_hint)
        if signed_url:
            return jsonify({"url": signed_url}), 200
        else:
            return jsonify({"error": "Failed to generate image"}), 500
    except Exception as e:
        logger.error(f"Error in generate_image_endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/generate_image_v2', methods=['POST'])
def generate_image_v2_endpoint():
    """Enhanced image generation endpoint with aspect ratio, consistency, and quality options."""
    try:
        start_time = time.time()
        data = request.get_json()
        prompt = data.get('prompt', '')
        level = data.get('level', 'Standard')
        image_style = data.get('image_style', None)
        aspect_ratio = data.get('aspect_ratio', None)  # square, landscape, portrait
        consistency_mode = data.get('consistency_mode', False)
        story_id = data.get('story_id', None)
        character_name = data.get('character_name', None)
        use_cache = data.get('use_cache', True)
        quality = data.get('quality', 'high')  # high, medium, low

        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400
        
        if not is_safe_prompt(prompt, level):
            return jsonify({"error": "Prompt contains inappropriate content"}), 400

        filename = generate_unique_image_filename(prompt, level=level, style_hint=image_style, prefix="img_v2")
        
        # Build consistency prompt if needed
        consistency_prompt = None
        if consistency_mode and story_id and character_name:
            char_ref = consistency_manager.get_character_reference(story_id, character_name)
            if char_ref:
                consistency_prompt = f"Maintain consistent character appearance: {char_ref['description']}"
        
        signed_url = generate_and_save_image(
            prompt, 
            filename, 
            retries=2,
            level=level, 
            style_hint=image_style,
            aspect_ratio=aspect_ratio,
            consistency_prompt=consistency_prompt,
            story_id=story_id,
            character_name=character_name,
            use_cache=use_cache
        )
        
        generation_time = time.time() - start_time
        
        if signed_url:
            return jsonify({
                "url": signed_url,
                "metadata": {
                    "generation_time": round(generation_time, 2),
                    "model_used": "gemini-3.0-pro-exp",  # This would be tracked in actual implementation
                    "aspect_ratio": aspect_ratio,
                    "cached": False  # Would be tracked in actual implementation
                }
            }), 200
        else:
            return jsonify({"error": "Failed to generate image"}), 500
    except Exception as e:
        logger.error(f"Error in generate_image_v2_endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/generate_consistent_image', methods=['POST'])
def generate_consistent_image_endpoint():
    """Generate image with character/style consistency using reference images."""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        story_id = data.get('story_id', None)
        character_name = data.get('character_name', None)
        content_id = data.get('content_id', None)
        style_name = data.get('style_name', None)
        level = data.get('level', 'Standard')
        image_style = data.get('image_style', None)
        aspect_ratio = data.get('aspect_ratio', None)
        reference_image_urls = data.get('reference_image_urls', [])  # List of URLs for blending

        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400
        
        if not story_id and not content_id:
            return jsonify({"error": "Either story_id or content_id required for consistency"}), 400

        # Build consistency prompt using ConsistencyManager
        consistency_prompt = consistency_manager.build_consistency_prompt(
            prompt,
            story_id=story_id,
            character_name=character_name,
            content_id=content_id,
            style_name=style_name
        )

        filename = generate_unique_image_filename(prompt, level=level, style_hint=image_style, prefix="consistent")
        
        # For Nano Banana Pro features, we would pass reference_image_urls here
        # This would enable image blending capabilities (up to 14 images)
        # Note: Actual implementation would require API support for reference images
        
        signed_url = generate_and_save_image(
            prompt,
            filename,
            retries=2,
            level=level,
            style_hint=image_style,
            aspect_ratio=aspect_ratio,
            consistency_prompt=consistency_prompt,
            story_id=story_id,
            character_name=character_name,
            use_cache=False  # Don't cache consistency-specific images
        )
        
        if signed_url:
            # Register character/style if provided for future consistency
            if story_id and character_name:
                consistency_manager.register_character(story_id, character_name, prompt, signed_url)
            if content_id and style_name:
                consistency_manager.register_style(content_id, style_name, {
                    "description": image_style or "default",
                    "reference_url": signed_url
                })
            
            return jsonify({
                "url": signed_url,
                "consistency_applied": True
            }), 200
        else:
            return jsonify({"error": "Failed to generate consistent image"}), 500
    except Exception as e:
        logger.error(f"Error in generate_consistent_image_endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/generate_lecture', methods=['POST'])
def generate_lecture_endpoint():
    """Endpoint to generate a lecture with audio and images from input text."""
    try:
        data = request.get_json()
        input_text = data.get('text', '')
        level = data.get('level', 'moderate')
        image_style = data.get('image_style', None)

        if not input_text:
            return jsonify({"error": "No text provided for lecture generation"}), 400

        # Generate request ID for progress tracking
        request_id = str(uuid4())
        
        # Initialize progress tracking
        request_progress[request_id] = {
            'step': 'Starting lecture generation...',
            'step_number': 0,
            'total_steps': 5,  # Script generation + audio generation + image generation
            'details': '',
            'last_updated': datetime.now().isoformat(),
            'progress_percentage': 0
        }
        request_start_times[request_id] = datetime.now()

        logger.info(f"Generating lecture for text length: {len(input_text)}, level: {level}, request_id: {request_id}")

        # Generate lecture script
        update_request_progress(request_id, "Generating lecture script", 1, 5, "Creating structured content")
        lecture_json = generate_lecture_script(input_text)
        if not lecture_json:
            cleanup_request_progress(request_id)
            return jsonify({"error": "Failed to generate lecture script"}), 500

        # Generate audio files and images
        update_request_progress(request_id, "Generating audio and images", 2, 5, "Processing lecture content")
        result = generate_lecture_audio_and_images(lecture_json, level=level, image_style=image_style)
        if not result:
            cleanup_request_progress(request_id)
            return jsonify({"error": "Failed to generate lecture audio and images"}), 500

        update_request_progress(request_id, "Lecture generation complete", 5, 5, f"Generated {len(result['audio_files'])} audio files")
        cleanup_request_progress(request_id)
        return jsonify({
            "lecture": result["lecture_data"],
            "audio_files": result["audio_files"],
            "lecture_id": result["lecture_id"],
            "request_id": request_id
        }), 200

    except Exception as e:
        logger.error(f"Error in generate_lecture_endpoint: {str(e)}")
        if 'request_id' in locals():
            cleanup_request_progress(request_id)
        return jsonify({"error": str(e)}), 500

<<<<<<< HEAD
@app.route('/generate_tts', methods=['POST'])
def generate_tts_endpoint():
    """
    Generate text-to-speech audio using Gemini 2.5 Flash Preview TTS model.
    
    This endpoint uses Google Cloud TTS with Chirp3 HD voices to provide
    high-quality, friendly narration. The voice is optimized for storytelling
    and reading content to children, similar to a parent reading a bedtime story.
    
    When Gemini 2.5 Flash Preview TTS becomes available through the GenAI API,
    this endpoint can be updated to use it directly.
    """
    try:
        data = request.get_json()
        text = data.get('text', '')
        voice = data.get('voice', 'narrator')
        model = data.get('model', 'gemini-2.5-flash-preview-tts')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Limit text length to prevent very long audio files
        max_length = 50000  # ~50k characters
        if len(text) > max_length:
            text = text[:max_length] + "..."
            logger.warning(f"Text truncated to {max_length} characters for TTS")
        
        logger.info(f"🎙️ Generating TTS for text length: {len(text)}, voice: {voice}, model: {model}")
        
        # Generate unique filename
        filename = f"tts_{uuid4().hex}.mp3"
        local_filepath = f"/tmp/{filename}"
        
        # Use Google Cloud TTS with Chirp3 HD voices
        # These voices are high-quality and friendly, perfect for narration
        # Voice selection optimized for storytelling:
        # - Aoede: Warm, friendly narrator voice (like a parent reading)
        # - Autonoe: Alternative voice for character dialogue
        voice_name = "en-US-Chirp3-HD-Aoede"  # Friendly, warm voice for narration
        if voice == "character":
            voice_name = "en-US-Chirp3-HD-Autonoe"  # Different voice for characters
        
        # Generate TTS audio
        success = text_to_speech(text, local_filepath, voice_name)
        
        if not success:
            return jsonify({"error": "Failed to generate TTS audio"}), 500
        
        # Upload to GCS
        blob = bucket.blob(f"tts/{filename}")
        blob.upload_from_filename(local_filepath)
        blob.make_public()
        
        # Get signed URL (valid for 1 hour)
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(hours=1),
            method="GET"
        )
        
        # Clean up local file
        import os
        if os.path.exists(local_filepath):
            os.remove(local_filepath)
        
        logger.info(f"✅ TTS audio generated and uploaded: {signed_url}")
        
        return jsonify({
            "audio_url": signed_url,
            "voice": voice,
            "model": model,
            "text_length": len(text)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in generate_tts_endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/character_chat', methods=['POST'])
def character_chat_endpoint():
    """Generate character responses for interactive character chat."""
    try:
        data = request.get_json()
        character_name = data.get('character_name', '')
        character_description = data.get('character_description', '')
        character_dialogue_examples = data.get('character_dialogue_examples', [])
        comic_title = data.get('comic_title', '')
        comic_theme = data.get('comic_theme', '')
        user_message = data.get('user_message', '')
        conversation_history = data.get('conversation_history', [])
        
        if not character_name or not user_message:
            return jsonify({"error": "Character name and user message required"}), 400
        
        logger.info(f"Generating character chat response for {character_name}")
        
        # Build character context
        character_context = f"""
Character Name: {character_name}
Description: {character_description}
Story: {comic_title}
Theme: {comic_theme}

Character's dialogue examples from the story:
"""
        for dialogue in character_dialogue_examples[:5]:  # Limit to 5 examples
            character_context += f"- \"{dialogue}\"\n"
        
        # Build conversation history context
        history_context = ""
        if conversation_history:
            history_context = "\nRecent conversation:\n"
            for msg in conversation_history[-6:]:  # Last 6 messages
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                history_context += f"{role.capitalize()}: {content}\n"
        
        # Build prompt for Gemini
        prompt = f"""You are {character_name}, a character from the comic "{comic_title}".

{character_context}

{history_context}

User asks: "{user_message}"

Respond as {character_name} would. Stay in character, be friendly and engaging. 
Keep your response concise (2-3 sentences max), natural, and appropriate for a children's story.
Do not break character or mention that you're an AI. Just respond as the character naturally would.

{character_name}:"""
        
        try:
            # Generate response using Gemini with config for more creative responses
            config_params = {
                'temperature': 0.8,  # More creative, natural responses
            }
            
            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-04-17",
                contents=prompt,
                config=types.GenerateContentConfig(**config_params) if config_params else None
            )
            
            # Extract text from response
            if hasattr(response, 'text'):
                response_text = response.text.strip()
            else:
                # Fallback: extract from candidates
                if response.candidates and response.candidates[0].content.parts:
                    text_part = next((p for p in response.candidates[0].content.parts if hasattr(p, 'text')), None)
                    response_text = text_part.text.strip() if text_part else ""
                else:
                    response_text = ""
            
            # Clean up response (remove character name if it's repeated)
            if response_text.startswith(character_name + ":"):
                response_text = response_text[len(character_name) + 1:].strip()
            
            logger.info(f"✅ Character chat response generated for {character_name}")
            
            return jsonify({
                "response": response_text,
                "character": character_name
            }), 200
            
        except Exception as e:
            logger.error(f"Error generating character response: {str(e)}")
            return jsonify({"error": f"Failed to generate character response: {str(e)}"}), 500
        
    except Exception as e:
        logger.error(f"Error in character_chat_endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500
=======
# --- Comic Generation Prompt Template ---
COMIC_GENERATION_PROMPT_TEMPLATE = '''You are an expert comic scriptwriter and visual storyteller. Given the following text, break it down into a short comic. Your output must:
- Extract the main characters and create a character_style_guide (describe each character's visual style, clothing, colors, and unique features, one per line, key is character name).
- Identify the overall theme and tone.
- Break the story into **7-10 panels** (scenes). For each panel, provide:
    - panel_id (numbered sequentially)
    - scene (short description of what's happening)
    - image_prompt (detailed visual prompt for the panel, including style, setting, mood, and referencing the character_style_guide for consistency)
    - dialogue (dictionary: character name -> what they say; can include Narrator)
- Output a single JSON object with keys: comic_title, theme, character_style_guide, panel_layout (list of panels as described).
- Do not include any explanations or markdown, just the JSON object.

Text:
"""{input_text}"""
'''

# --- Two-Step Comic Generation ---
COMIC_CHARACTERS_PROMPT_TEMPLATE = '''You are an expert comic scriptwriter. Given the following text, extract the main characters and create a character style guide.

Your output must be a JSON object with:
- comic_title: A catchy title for the comic
- theme: The overall theme and tone
- character_style_guide: A dictionary where each key is a character name and value is their visual description (clothing, colors, unique features)

Text:
"""{input_text}"""
'''

COMIC_PANELS_PROMPT_TEMPLATE = '''You are an expert comic scriptwriter. Given the following text and character information, create 7-20 comic panels to tell the story effectively.

Character Style Guide:
{character_style_guide}

Theme: {theme}

Your output must be a JSON array of panel objects, each with:
- panel_id: sequential number
- scene: short description of what's happening
- image_prompt: detailed visual prompt for the panel (NO TEXT, NO CAPTIONS, NO SPEECH BUBBLES)
- dialogue: dictionary of character name -> what they say (REQUIRED - each panel should have meaningful dialogue)

IMPORTANT DIALOGUE REQUIREMENTS:
- Each panel MUST have dialogue from at least one character
- Dialogue should be natural, engaging, and advance the story
- Use character names from the character_style_guide
- Make dialogue conversational and appropriate to the scene
- Do NOT use generic phrases like "Panel X dialogue"
- Examples of good dialogue:
  * "Wow, this is amazing!" (excitement)
  * "Let me try this..." (action)
  * "I can see everything clearly now!" (discovery)
  * "This feels so natural!" (satisfaction)

IMPORTANT: 
- Generate 7-20 panels based on story complexity
- Each panel MUST have dialogue from at least one character
- Image prompts should NOT include any text, captions, or speech bubbles
- Make dialogue natural and engaging

Text:
"""{input_text}"""
'''

def extract_json_from_response(text):
    """Extract the first JSON object or array from a string, ignoring preamble or code block markers."""
    # Remove code block markers if present
    text = text.strip()
    if text.startswith('```json'):
        text = text[len('```json'):].strip()
    if text.startswith('```'):
        text = text[len('```'):].strip()
    if text.endswith('```'):
        text = text[:-3].strip()
    # Find the first JSON object or array
    match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
    if match:
        return match.group(1)
    return text  # fallback: return as-is

def generate_comic_script(input_text: str) -> dict:
    """Call the first model to generate the comic breakdown and character style guide."""
    try:
        # Step 1: Generate characters and theme
        logger.info("Step 1: Generating characters and theme")
        characters_prompt = COMIC_CHARACTERS_PROMPT_TEMPLATE.format(input_text=input_text)
        characters_response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=characters_prompt,
            config=types.GenerateContentConfig(
                system_instruction="You are an expert comic scriptwriter."
            )
        )
        
        # Improved response handling with better error checking
        characters_text = None
        if characters_response:
            # Try to get text from response
            if hasattr(characters_response, 'text') and characters_response.text:
                characters_text = characters_response.text
            elif (hasattr(characters_response, 'candidates') and 
                  characters_response.candidates and 
                  len(characters_response.candidates) > 0 and
                  hasattr(characters_response.candidates[0], 'content') and
                  characters_response.candidates[0].content and
                  hasattr(characters_response.candidates[0].content, 'parts') and
                  characters_response.candidates[0].content.parts and
                  len(characters_response.candidates[0].content.parts) > 0 and
                  hasattr(characters_response.candidates[0].content.parts[0], 'text')):
                characters_text = characters_response.candidates[0].content.parts[0].text
        
        if not characters_text:
            logger.error("No text in characters model response or response is None.")
            return None
        
        print(f"\n=== STEP 1: CHARACTERS RESPONSE ===\n{characters_text}\n")
        logger.info(f"Characters response length: {len(characters_text)} characters")
        
        # Extract JSON from response
        characters_text = extract_json_from_response(characters_text)
        
        try:
            characters_data = json.loads(characters_text)
            print(f"\n=== STEP 1: PARSED CHARACTERS DATA ===\n{json.dumps(characters_data, indent=2)}\n")

            # --- ROBUSTNESS FIX ---
            # The AI sometimes returns a dictionary for the character description instead of a string.
            # This block checks for that and flattens the dictionary into a string to match the expected format.
            style_guide = characters_data.get('character_style_guide', {})
            if isinstance(style_guide, dict):
                for char_name, details in style_guide.items():
                    if isinstance(details, dict):
                        # Flatten the dictionary of details into a single descriptive string
                        description_str = ", ".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in details.items()])
                        style_guide[char_name] = description_str
                        logger.info(f"Flattened character style guide for '{char_name}' into a string.")
            # --- END FIX ---

        except Exception as e:
            logger.error(f"Failed to parse characters JSON: {e}. Raw: {characters_text[:500]}")
            return None
        
        # Step 2: Generate panels using the characters
        logger.info("Step 2: Generating panels")
        character_style_guide_str = json.dumps(characters_data.get('character_style_guide', {}))
        panels_prompt = COMIC_PANELS_PROMPT_TEMPLATE.format(
            input_text=input_text,
            character_style_guide=character_style_guide_str,
            theme=characters_data.get('theme', 'Adventure')
        )
        
        panels_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=panels_prompt,
            config=types.GenerateContentConfig(
                system_instruction="You are an expert comic scriptwriter. You MUST generate meaningful, natural dialogue for each panel. Each panel should have at least one character speaking with engaging, story-advancing dialogue. Do not create empty dialogue objects or use generic phrases. Generate 7-20 panels based on story complexity. Make dialogue conversational and appropriate to each scene."
            )
        )
        
        # Improved response handling with better error checking
        panels_text = None
        if panels_response:
            # Try to get text from response
            if hasattr(panels_response, 'text') and panels_response.text:
                panels_text = panels_response.text
            elif (hasattr(panels_response, 'candidates') and 
                  panels_response.candidates and 
                  len(panels_response.candidates) > 0 and
                  hasattr(panels_response.candidates[0], 'content') and
                  panels_response.candidates[0].content and
                  hasattr(panels_response.candidates[0].content, 'parts') and
                  panels_response.candidates[0].content.parts and
                  len(panels_response.candidates[0].content.parts) > 0 and
                  hasattr(panels_response.candidates[0].content.parts[0], 'text')):
                panels_text = panels_response.candidates[0].content.parts[0].text
        
        if not panels_text:
            logger.error("No text in panels model response or response is None.")
            return None
        
        print(f"\n=== STEP 2: PANELS RESPONSE ===\n{panels_text}\n")
        logger.info(f"Panels response length: {len(panels_text)} characters")
        
        # Extract JSON from response
        panels_text = extract_json_from_response(panels_text)
        
        panels_data = None
        # Try multiple approaches to parse the panels JSON
        try:
            # First attempt: direct parsing
            panels_data = json.loads(panels_text)
            print(f"\n=== STEP 2: PARSED PANELS DATA ===\n{json.dumps(panels_data, indent=2)}\n")
            logger.info("Successfully parsed panels JSON on first attempt")
        except Exception as e:
            logger.error(f"Failed to parse panels JSON: {e}. Raw: {panels_text[:500]}")
            
            # Second attempt: try to fix truncated JSON
            try:
                fixed_panels_text = fix_truncated_panels_json(panels_text)
                print(f"\n=== STEP 2: FIXED PANELS JSON ===\n{fixed_panels_text}\n")
                panels_data = json.loads(fixed_panels_text)
                print(f"\n=== STEP 2: PARSED FIXED PANELS DATA ===\n{json.dumps(panels_data, indent=2)}\n")
                logger.info("Successfully fixed and parsed truncated panels JSON")
            except Exception as e2:
                logger.error(f"Still failed to parse panels JSON after fixing: {e2}")
                
                # Third attempt: try to extract partial panels from the JSON
                try:
                    panels_data = extract_partial_panels(panels_text, characters_data.get('character_style_guide', {}))
                    if panels_data:
                        print(f"\n=== STEP 2: EXTRACTED PARTIAL PANELS ===\n{json.dumps(panels_data, indent=2)}\n")
                        logger.info(f"Successfully extracted {len(panels_data)} partial panels")
                    else:
                        # Last resort: create fallback panels
                        panels_data = create_fallback_panels(panels_text, characters_data.get('character_style_guide', {}))
                        print(f"\n=== STEP 2: FALLBACK PANELS DATA ===\n{json.dumps(panels_data, indent=2)}\n")
                        if not panels_data:
                            return None
                except Exception as e3:
                    logger.error(f"Failed to extract partial panels: {e3}")
                    # Last resort: create fallback panels
                    panels_data = create_fallback_panels(panels_text, characters_data.get('character_style_guide', {}))
                    print(f"\n=== STEP 2: FALLBACK PANELS DATA ===\n{json.dumps(panels_data, indent=2)}\n")
                    if not panels_data:
                        return None
        
        # --- LIMIT PANELS TO 10 ---
        # MAX_PANELS = 10
        # if isinstance(panels_data, list) and len(panels_data) > MAX_PANELS:
        #     logger.info(f"Limiting parsed panels to {MAX_PANELS}")
        #     panels_data = panels_data[:MAX_PANELS]
        
        # Combine the data
        comic_data = {
            "comic_title": characters_data.get('comic_title', 'Generated Comic'),
            "theme": characters_data.get('theme', 'Adventure'),
            "character_style_guide": characters_data.get('character_style_guide', {}),
            "panel_layout": panels_data if isinstance(panels_data, list) else []
        }
        
        # Post-process to fix any generic dialogues
        if comic_data['panel_layout']:
            character_names = list(comic_data['character_style_guide'].keys()) if comic_data['character_style_guide'] else ["Character"]
            for panel in comic_data['panel_layout']:
                dialogue = panel.get('dialogue', {})
                # Check if dialogue is generic
                if dialogue:
                    for character, text in dialogue.items():
                        if "Panel" in text and "dialogue" in text:
                            # Replace with meaningful dialogue
                            panel['dialogue'] = generate_meaningful_dialogue(
                                panel.get('scene', ''), 
                                character_names, 
                                panel.get('panel_id', 1)
                            )
                            break
        
        print(f"\n=== FINAL COMIC DATA ===\n{json.dumps(comic_data, indent=2)}\n")
        logger.info(f"Successfully generated comic with {len(comic_data['panel_layout'])} panels")
        return comic_data
        
    except Exception as e:
        logger.error(f"Error in two-step comic generation: {e}")
        return None


def extract_partial_panels(partial_panels_json: str, character_style_guide: dict) -> list:
    """Extract partial panels from truncated JSON response, always using whatever dialogue is present. Only use fallback if no panels can be extracted."""
    logger.info("Attempting to extract partial panels from truncated JSON")
    print(f"=== EXTRACTING PARTIAL PANELS ===")
    print(f"Partial JSON: {partial_panels_json[:500]}...")
    
    panels = []
    character_names = list(character_style_guide.keys()) if character_style_guide else ["Character"]
    
    # Pattern: extract panel_id, scene, image_prompt, and dialogue (as much as possible)
    panel_pattern = r'\{[^{}]*"panel_id":\s*(\d+)[^{}]*"scene":\s*"([^"]*)"[^{}]*"image_prompt":\s*"([^"]*)"[^{}]*"dialogue":\s*\{([^}]*)\}'
    matches = re.findall(panel_pattern, partial_panels_json, re.DOTALL)
    print(f"Found {len(matches)} panel matches using regex")
    for match in matches:
        panel_id, scene, image_prompt, dialogue_block = match
        # Try to parse dialogue block as a dict
        dialogue = {}
        dialogue_items = re.findall(r'"([^"]+)":\s*"([^"]*)"', dialogue_block)
        for char, text in dialogue_items:
            dialogue[char] = text
        if not dialogue and character_names:
            dialogue = {character_names[0]: ""}
        panel = {
            "panel_id": int(panel_id),
            "scene": scene.strip(),
            "image_prompt": image_prompt.strip(),
            "dialogue": dialogue
        }
        panels.append(panel)
        print(f"Extracted panel {panel_id}: {scene[:50]}...")
    # If we found some panels, return them
    if panels:
        panels.sort(key=lambda x: x["panel_id"])
        for i, panel in enumerate(panels, 1):
            panel["panel_id"] = i
        print(f"Successfully extracted {len(panels)} partial panels")
        return panels
    # If no panels found, try to extract just the first panel from the beginning
    print("No complete panels found, trying to extract first panel...")
    first_panel_start = partial_panels_json.find('"panel_id": 1')
    if first_panel_start != -1:
        scene_match = re.search(r'"scene":\s*"([^"]*)"', partial_panels_json[first_panel_start:])
        prompt_match = re.search(r'"image_prompt":\s*"([^"]*)"', partial_panels_json[first_panel_start:])
        dialogue_match = re.search(r'"dialogue":\s*\{([^}]*)\}', partial_panels_json[first_panel_start:])
        dialogue = {}
        if dialogue_match:
            dialogue_items = re.findall(r'"([^"]+)":\s*"([^"]*)"', dialogue_match.group(1))
            for char, text in dialogue_items:
                dialogue[char] = text
        if scene_match and prompt_match:
            panel = {
                "panel_id": 1,
                "scene": scene_match.group(1).strip(),
                "image_prompt": prompt_match.group(1).strip(),
                "dialogue": dialogue if dialogue else {character_names[0]: ""}
            }
            panels.append(panel)
            print(f"Extracted first panel: {panel['scene'][:50]}...")
            return panels
    print("Could not extract any partial panels")
    return []

def generate_comic_panel_images(comic_data, level="moderate", image_style=None):
    """Generate images for each panel in batches to prevent memory overflow."""
    if not comic_data or 'panel_layout' not in comic_data or 'character_style_guide' not in comic_data:
        logger.error("Comic data missing panel_layout or character_style_guide.")
        return None
    
    # Check initial memory
    initial_memory = check_memory_and_cleanup()
    logger.info(f"Starting comic panel generation with memory: {initial_memory:.1f} MB")
    
    # Allow unlimited panels (removed MAX_PANELS limit)
    # MAX_PANELS = 8
    panels = comic_data['panel_layout']
    # if len(panels) > MAX_PANELS:
    #     logger.warning(f"Too many panels ({len(panels)}), limiting to {MAX_PANELS} to prevent memory overflow")
    #     panels = panels[:MAX_PANELS]
    #     comic_data['panel_layout'] = panels
    
    style_guide = comic_data['character_style_guide']
    style_guide_str = '\n'.join([f"{k}: {v}" for k, v in style_guide.items()]) if isinstance(style_guide, dict) else str(style_guide)
    comic_style_enhancer = "Comic style, bright, vibrant, good colors, visually appealing, dynamic composition, expressive characters. IMPORTANT: NO TEXT, NO CAPTIONS, NO SPEECH BUBBLES, NO WRITING in the image - only visual art."
    
    # Process panels one at a time to minimize memory usage
    BATCH_SIZE = 1  # Process one panel at a time to prevent memory overflow
    total_panels = len(panels)
    
    logger.info(f"Starting single-panel processing for {total_panels} panels")
    
    for panel_idx, panel in enumerate(panels):
        panel_num = panel_idx + 1
        logger.info(f"Processing panel {panel_num}/{total_panels}")
        
        # Check memory before each panel
        current_memory = check_memory_and_cleanup()
        if current_memory > MEMORY_LIMIT_MB:
            logger.error(f"Memory usage too high ({current_memory:.1f} MB) for panel {panel_num}. Skipping remaining panels.")
            break
        
        base_prompt = panel.get('image_prompt', '')
        full_prompt = f"{base_prompt}\nCharacter Style Guide:\n{style_guide_str}\n{comic_style_enhancer}"
        # Use panel_num (actual index) instead of panel_id to ensure unique filenames
        filename = generate_unique_image_filename(full_prompt, level=level, style_hint=image_style, prefix=f"comic_panel_{panel_num}")
        
        print(f"\n=== GENERATING PANEL {panel_num} ===")
        print(f"Panel ID: {panel.get('panel_id', 'N/A')}")
        print(f"Scene: {panel.get('scene', 'N/A')}")
        print(f"Image Prompt: {base_prompt[:100]}...")
        print(f"Filename: {filename}")
        print(f"Current Memory: {current_memory:.1f} MB")
        
        url = generate_and_save_image(full_prompt, filename, level=level, style_hint=image_style)
        panel['image_url'] = url
        
        print(f"Generated URL: {url[:80]}...")
        
        # Aggressive memory cleanup after each image
        gc.collect()
        
        # Monitor memory usage
        memory_mb = get_memory_usage()
        logger.info(f"Memory usage after panel {panel_num}: {memory_mb:.1f} MB")
        if memory_mb > MEMORY_WARNING_MB:
            logger.warning(f"High memory usage after panel {panel_num}: {memory_mb:.1f} MB")
        
        # Longer delay between panels to allow memory cleanup
        if panel_num < total_panels:  # Don't delay after the last panel
            logger.info(f"Panel {panel_num} complete. Waiting 5 seconds before next panel...")
            time.sleep(5)  # Increased delay for better memory cleanup
    
    final_memory = get_memory_usage()
    logger.info(f"Completed processing for all {total_panels} panels. Final memory: {final_memory:.1f} MB")
    return comic_data


@app.route('/generate_comic', methods=['POST'])
def generate_comic_endpoint():
    """Enhanced endpoint to generate a comic with robust error handling and frontend compatibility"""
    request_id = str(uuid4())
    
    try:
        # Validate request
        if not request.is_json:
            return jsonify(create_frontend_compatible_response(
                success=False,
                error="Request must be JSON",
                request_id=request_id
            )), 400
        
        data = request.get_json()
        input_text = data.get('text', '')
        level = data.get('level', 'moderate')
        image_style = data.get('image_style', None)
        user_token = data.get('user_token', None)
        
        if not input_text:
            return jsonify(create_frontend_compatible_response(
                success=False,
                error="No text provided for comic generation",
                request_id=request_id
            )), 400
        
        # Initialize progress tracking
        request_progress[request_id] = {
            'step': 'Starting comic generation...',
            'step_number': 0,
            'total_steps': 5,
            'details': '',
            'last_updated': datetime.now().isoformat(),
            'progress_percentage': 0
        }
        request_start_times[request_id] = datetime.now()
        
        # Store user token for notifications
        if user_token:
            request_user_tokens[request_id] = user_token
        
        logger.info(f"Comic generation started - Request ID: {request_id}, Text length: {len(input_text)}, Level: {level}")
        
        # Step 1: Generate comic script
        update_request_progress(request_id, "Generating comic script", 1, 5, "Creating characters and story")
        comic_data = generate_comic_script_robust(input_text)
        
        if not comic_data or not comic_data.get('panel_layout'):
            return jsonify(create_frontend_compatible_response(
                success=False,
                error="Failed to generate comic script",
                request_id=request_id
            )), 500
        
        panel_count = len(comic_data.get('panel_layout', []))
        update_request_progress(request_id, "Comic script complete", 2, 5, f"Generated {panel_count} panels")
        
        # Step 2: Generate images
        update_request_progress(request_id, "Generating panel images", 3, 5, f"Processing {panel_count} panels")
        comic_with_images = generate_comic_panel_images(comic_data, level=level, image_style=image_style)
        
        if not comic_with_images:
            return jsonify(create_frontend_compatible_response(
                success=False,
                error="Failed to generate comic panel images",
                request_id=request_id
            )), 500
        
        final_panel_count = len(comic_with_images.get('panel_layout', []))
        update_request_progress(request_id, "Comic generation complete", 5, 5, f"Successfully generated {final_panel_count} panels with images")
        
        # Send completion notification
        if user_token:
            send_push_notification(
                user_token,
                "Comic Ready! 🎨",
                f"Your {final_panel_count}-panel comic is complete",
                {'request_id': request_id, 'type': 'comic', 'panel_count': str(final_panel_count)}
            )
        
        # Update Firebase task status
        update_firebase_task_status(request_id, 'completed', {'comic': comic_with_images})
        
        # Clean up progress tracking
        cleanup_request_progress(request_id)
        
        # Return success response
        return jsonify(create_frontend_compatible_response(
            success=True,
            data={"comic": comic_with_images},
            request_id=request_id
        )), 200
        
    except Exception as e:
        logger.error(f"Comic generation failed - Request ID: {request_id}: {str(e)}")
        
        # Send error notification
        if user_token:
            send_push_notification(
                user_token,
                "Comic Generation Failed",
                "There was an error generating your comic. Please try again.",
                {'request_id': request_id, 'type': 'comic_error'}
            )
        
        # Update Firebase task status
        update_firebase_task_status(request_id, 'failed', error_message=str(e))
        
        # Clean up progress tracking
        cleanup_request_progress(request_id)
        
        return jsonify(create_frontend_compatible_response(
            success=False,
            error=f"An unexpected error occurred: {str(e)}",
            request_id=request_id
        )), 500

def fix_truncated_panels_json(json_str: str) -> str:
    """Attempt to fix truncated panels JSON by completing incomplete objects."""
    print(f"=== FIXING TRUNCATED JSON ===")
    print(f"Original: {json_str[:200]}...")
    
    # Count braces and brackets to see if they're balanced
    open_braces = json_str.count('{')
    close_braces = json_str.count('}')
    open_brackets = json_str.count('[')
    close_brackets = json_str.count(']')
    
    print(f"Braces: {open_braces} open, {close_braces} close")
    print(f"Brackets: {open_brackets} open, {close_brackets} close")
    
    # If braces/brackets are balanced, try to parse as-is
    if open_braces == close_braces and open_brackets == close_brackets:
        print("Braces and brackets are balanced, attempting to parse as-is")
        return json_str
    
    # Try to find complete panel objects
    panel_pattern = r'\{[^{}]*"panel_id":\s*\d+[^{}]*"scene":\s*"[^"]*"[^{}]*"image_prompt":\s*"[^"]*"[^{}]*\}'
    complete_panels = re.findall(panel_pattern, json_str, re.DOTALL)
    
    if complete_panels:
        print(f"Found {len(complete_panels)} complete panel objects")
        # Reconstruct JSON with only complete panels
        fixed_json = "[\n" + ",\n".join(complete_panels) + "\n]"
        print(f"Fixed JSON: {fixed_json[:200]}...")
        return fixed_json
    
    # If no complete panels found, try to complete the last incomplete panel
    print("No complete panels found, attempting to complete last incomplete panel")
    
    # Find the last opening brace
    last_open_brace = json_str.rfind('{')
    if last_open_brace != -1:
        # Find the last panel_id
        panel_id_match = re.search(r'"panel_id":\s*(\d+)', json_str[last_open_brace:])
        if panel_id_match:
            panel_id = panel_id_match.group(1)
            
            # Try to extract scene and image_prompt from the incomplete panel
            scene_match = re.search(r'"scene":\s*"([^"]*)"', json_str[last_open_brace:])
            prompt_match = re.search(r'"image_prompt":\s*"([^"]*)"', json_str[last_open_brace:])
            
            if scene_match and prompt_match:
                # Complete the panel
                incomplete_panel = json_str[last_open_brace:]
                completed_panel = incomplete_panel.rstrip(',\n\r\t ') + '}'
                
                # Find all complete panels before this one
                before_incomplete = json_str[:last_open_brace]
                complete_panels_before = re.findall(panel_pattern, before_incomplete, re.DOTALL)
                
                # Reconstruct JSON
                all_panels = complete_panels_before + [completed_panel]
                fixed_json = "[\n" + ",\n".join(all_panels) + "\n]"
                print(f"Completed last panel and fixed JSON: {fixed_json[:200]}...")
                return fixed_json
    
    # If all else fails, return the original with balanced braces
    print("Could not fix JSON, returning original with balanced braces")
    fixed_json = json_str.rstrip(',\n\r\t ')
    
    # Add missing closing braces/brackets
    while fixed_json.count('{') > fixed_json.count('}'):
        fixed_json += '}'
    while fixed_json.count('[') > fixed_json.count(']'):
        fixed_json += ']'
    
    print(f"Final fixed JSON: {fixed_json[:200]}...")
    return fixed_json

def create_fallback_panels(partial_panels_json: str, character_style_guide: dict) -> list:
    """Create fallback panels when panels JSON is truncated or malformed."""
    logger.warning("Creating fallback panels due to JSON parsing failure")
    print(f"=== CREATING FALLBACK PANELS ===")
    print(f"Partial JSON: {partial_panels_json[:500]}...")
    print(f"Character Style Guide: {character_style_guide}")
    
    panels = []
    
    # Try to extract partial panels from the JSON first
    extracted_panels = extract_partial_panels(partial_panels_json, character_style_guide)
    if extracted_panels:
        logger.info(f"Extracted {len(extracted_panels)} partial panels from truncated JSON")
        return extracted_panels
    
    logger.info("Extracted 0 partial panels from truncated JSON")
    logger.info("Creating basic fallback panels based on character style guide")
    
    # Get character names from the style guide
    character_names = list(character_style_guide.keys())
    if not character_names:
        character_names = ["Character 1", "Character 2"]
    
    # Create meaningful fallback panels based on the characters (7-20 panels)
    fallback_scenes = [
        f"Introduction scene showing {', '.join(character_names[:2])} in their environment",
        f"Action scene with {character_names[0]} and {character_names[1] if len(character_names) > 1 else 'other characters'} in motion",
        f"Close-up scene focusing on {character_names[0]}'s expressions and reactions",
        f"Wide shot showing the environment and all characters interacting",
        f"Dramatic moment with {', '.join(character_names[:2])} facing a challenge together",
        f"Discovery scene where {character_names[0]} finds something important",
        f"Conflict resolution with {', '.join(character_names[:2])} working together",
        f"Celebration scene with all characters sharing their success",
        f"Reflection moment with {character_names[0]} thinking about the journey",
        f"Future planning scene with characters discussing next steps"
    ]
    
    # Add more scenes if we have more characters
    if len(character_names) > 2:
        fallback_scenes.extend([
            f"Conflict scene with {character_names[2]} causing chaos",
            f"Resolution scene with all characters working together",
            f"Character development scene with {character_names[1]} showing growth",
            f"Team building moment with all characters bonding"
        ])
    
    # Ensure we have 7-20 panels
    if len(fallback_scenes) < 7:
        # Add more generic scenes to reach minimum
        for i in range(7 - len(fallback_scenes)):
            fallback_scenes.append(f"Additional scene {i+1} with {character_names[0]} and others")
    elif len(fallback_scenes) > 20:
        # Limit to 20 panels
        fallback_scenes = fallback_scenes[:20]
    
    for i, scene in enumerate(fallback_scenes, 1):
        # Create a more detailed image prompt based on the character style guide
        character_descriptions = []
        for char_name, char_data in character_style_guide.items():
            if isinstance(char_data, dict) and 'description' in char_data:
                desc = char_data['description'][:100]  # Truncate long descriptions
                character_descriptions.append(f"{char_name}: {desc}")
        
        image_prompt = f"{scene}. "
        if character_descriptions:
            image_prompt += f"Character details: {'; '.join(character_descriptions[:2])}. "
        image_prompt += f"{', '.join(character_names[:2])} are prominently featured in this comic panel. NO TEXT, NO CAPTIONS, NO SPEECH BUBBLES."
        
        # Create meaningful dialogue for each panel
        dialogue = generate_meaningful_dialogue(scene, character_names, i)
        
        panel = {
            "panel_id": i,
            "scene": scene,
            "image_prompt": image_prompt,
            "dialogue": dialogue
        }
        panels.append(panel)
        print(f"Created fallback panel {i}: {scene}")
    
    print(f"Final fallback panels: {len(panels)} panels created")
    logger.info(f"Created {len(panels)} fallback panels")
    return panels

def upload_to_gcs(file_path, gcs_path, content_type="application/octet-stream"):
    """Safely upload a file to Google Cloud Storage"""
    try:
        # Initialize GCS if needed
        if not initialize_gcs():
            logger.error("❌ GCS client not available")
            return None
            
        blob = bucket.blob(gcs_path)
        with open(file_path, "rb") as file:
            blob.upload_from_file(file, content_type=content_type)
        
        # Generate signed URL
        expiration_time = timedelta(minutes=60)
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=expiration_time,
            method="GET"
        )
        
        logger.info(f"✅ File uploaded to GCS: {gcs_path}")
        return signed_url
        
    except Exception as e:
        logger.error(f"❌ Error uploading to GCS: {e}")
        return None

def upload_buffer_to_gcs(buffer, gcs_path, content_type="application/octet-stream"):
    """Safely upload a buffer to Google Cloud Storage"""
    try:
        # Initialize GCS if needed
        if not initialize_gcs():
            logger.error("❌ GCS client not available")
            return None
            
        blob = bucket.blob(gcs_path)
        buffer.seek(0)
        blob.upload_from_file(buffer, content_type=content_type)
        
        # Generate signed URL
        expiration_time = timedelta(minutes=60)
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=expiration_time,
            method="GET"
        )
        
        logger.info(f"✅ Buffer uploaded to GCS: {gcs_path}")
        return signed_url
        
    except Exception as e:
        logger.error(f"❌ Error uploading buffer to GCS: {e}")
        return None

def generate_meaningful_dialogue(scene: str, character_names: list, panel_id: int) -> dict:
    """Generate meaningful dialogue based on scene content and character names."""
    if not character_names:
        return {"Character": "Let's see what happens!"}
    
    # Extract key words from scene to understand context
    scene_lower = scene.lower()
    
    # Define dialogue patterns based on scene content with more variety
    dialogue_patterns = {
        "watching": ["I wonder what's happening?", "This looks interesting!", "What's going on here?", "Fascinating!", "I need to see more!"],
        "approaching": ["Let me get a closer look.", "I need to investigate this.", "Time to explore!", "Here I come!", "Getting closer..."],
        "jumping": ["Here I go!", "Up we go!", "Let's see what's up there!", "Jump!", "Flying high!"],
        "walking": ["One step at a time.", "I'm getting closer.", "Almost there!", "Walking...", "On my way!"],
        "typing": ["Click, click, click!", "I'm making progress!", "This is fun!", "Tap tap tap!", "I'm writing!"],
        "noticing": ["Oh! What's that?", "I see something interesting!", "Look at that!", "Hey!", "What's this?"],
        "staring": ["This is fascinating!", "I can't look away!", "So mesmerizing!", "Amazing!", "Incredible!"],
        "pressing": ["Click!", "Let's see what happens!", "Here goes nothing!", "Press!", "Action!"],
        "returning": ["I'm back!", "What did I miss?", "Let's see what changed!", "Home again!", "Back to work!"],
        "seeing": ["Wow! Look at that!", "This is unexpected!", "Incredible!", "Amazing!", "Fantastic!"],
        "looking": ["What do we have here?", "This is interesting!", "Fascinating!", "Let me see...", "Curious!"],
        "purring": ["I'm so satisfied!", "This is perfect!", "Mission accomplished!", "Purr...", "Happy!"],
        "satisfied": ["Perfect!", "I did it!", "Success!", "Great!", "Excellent!"],
        "focused": ["I need to concentrate.", "This is important.", "Let me focus.", "Pay attention!", "Focus!"],
        "curious": ["What's this?", "I want to know more!", "Tell me more!", "Curious!", "Interesting!"],
        "excited": ["This is amazing!", "I love this!", "Fantastic!", "Exciting!", "Wonderful!"],
        "surprised": ["Oh my!", "I didn't expect that!", "Wow!", "Surprising!", "Unexpected!"],
        "determined": ["I can do this!", "Nothing will stop me!", "I'm ready!", "Let's go!", "Determined!"],
        "happy": ["This makes me so happy!", "I love this!", "Perfect!", "Joy!", "Delight!"],
        "investigating": ["Let me check this out.", "I need to examine this.", "Investigating...", "Looking closely...", "Examining..."],
        "learning": ["I'm learning!", "This is new!", "Understanding!", "Getting it!", "Learning!"],
        "playing": ["This is fun!", "Playing around!", "Having fun!", "Enjoying this!", "Play time!"],
        "working": ["Hard at work!", "Getting things done!", "Working!", "Busy!", "Productive!"],
        "resting": ["Taking a break.", "Resting...", "Relaxing...", "Peaceful...", "Calm..."],
        "thinking": ["Hmm...", "Let me think...", "Interesting...", "Considering...", "Pondering..."]
    }
    
    # Find the most appropriate dialogue pattern
    selected_pattern = "curious"  # default
    for keyword, pattern in dialogue_patterns.items():
        if keyword in scene_lower:
            selected_pattern = keyword
            break
    
    # Get dialogue options for the pattern
    dialogue_options = dialogue_patterns.get(selected_pattern, ["This is interesting!"])
    
    # Select dialogue based on panel number and scene content for more variety
    dialogue_index = (panel_id + len(scene)) % len(dialogue_options)
    dialogue_text = dialogue_options[dialogue_index]
    
    # Use the first character name
    character_name = character_names[0] if character_names else "Character"
    
    return {character_name: dialogue_text}

# Enhanced error handling and response validation for frontend compatibility
def validate_comic_response(comic_data: dict) -> dict:
    """Validate and sanitize comic data to ensure frontend compatibility"""
    try:
        # Ensure all required fields are present with proper types
        validated_comic = {
            "comic_title": str(comic_data.get("comic_title", "Generated Comic")),
            "theme": str(comic_data.get("theme", "Adventure")),
            "character_style_guide": {},
            "panel_layout": []
        }
        
        # Validate character style guide - ALWAYS convert to string format
        style_guide = comic_data.get("character_style_guide", {})
        if isinstance(style_guide, dict):
            for char_name, details in style_guide.items():
                if isinstance(details, dict):
                    # Flatten dictionary to string for frontend compatibility
                    description_parts = []
                    for key, value in details.items():
                        if isinstance(value, str):
                            description_parts.append(f"{key.replace('_', ' ').title()}: {value}")
                        else:
                            description_parts.append(f"{key.replace('_', ' ').title()}: {str(value)}")
                    validated_comic["character_style_guide"][str(char_name)] = ", ".join(description_parts)
                elif isinstance(details, str):
                    validated_comic["character_style_guide"][str(char_name)] = details
                else:
                    # Fallback for unexpected types
                    validated_comic["character_style_guide"][str(char_name)] = str(details)
        
        # Validate panel layout
        panel_layout = comic_data.get("panel_layout", [])
        if isinstance(panel_layout, list):
            for i, panel in enumerate(panel_layout):
                if isinstance(panel, dict):
                    validated_panel = {
                        "panel_id": int(panel.get("panel_id", i + 1)),
                        "scene": str(panel.get("scene", f"Scene {i + 1}")),
                        "image_prompt": str(panel.get("image_prompt", "")),
                        "dialogue": {}
                    }
                    
                    # Validate dialogue
                    dialogue = panel.get("dialogue", {})
                    if isinstance(dialogue, dict):
                        for char_name, text in dialogue.items():
                            if isinstance(text, str) and text.strip():
                                validated_panel["dialogue"][str(char_name)] = text.strip()
                    
                    # Ensure at least one dialogue entry
                    if not validated_panel["dialogue"]:
                        char_names = list(validated_comic["character_style_guide"].keys())
                        if char_names:
                            validated_panel["dialogue"] = {char_names[0]: "Let's see what happens!"}
                        else:
                            validated_panel["dialogue"] = {"Character": "Let's see what happens!"}
                    
                    # Add image_url if present
                    if "image_url" in panel and panel["image_url"]:
                        validated_panel["image_url"] = str(panel["image_url"])
                    
                    validated_comic["panel_layout"].append(validated_panel)
        
        # Ensure minimum panel count
        if len(validated_comic["panel_layout"]) < 3:
            logger.warning(f"Comic has only {len(validated_comic['panel_layout'])} panels, creating fallback panels")
            fallback_panels = create_fallback_panels("", validated_comic["character_style_guide"])
            validated_comic["panel_layout"].extend(fallback_panels[:3 - len(validated_comic["panel_layout"])])
        
        logger.info(f"Validated comic with {len(validated_comic['panel_layout'])} panels and {len(validated_comic['character_style_guide'])} characters")
        return validated_comic
        
    except Exception as e:
        logger.error(f"Error validating comic data: {e}")
        # Return a safe fallback comic
        return {
            "comic_title": "Generated Comic",
            "theme": "Adventure",
            "character_style_guide": {"Character": "A brave adventurer"},
            "panel_layout": [
                {
                    "panel_id": 1,
                    "scene": "The adventure begins",
                    "image_prompt": "A character starting an adventure",
                    "dialogue": {"Character": "Let's begin our journey!"}
                }
            ]
        }

def create_frontend_compatible_response(success: bool, data: dict = None, error: str = None, request_id: str = None) -> dict:
    """Create a standardized response that the frontend can always parse"""
    response = {
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    
    if request_id:
        response["request_id"] = request_id
    
    if success and data:
        response.update(data)
    elif not success and error:
        response["error"] = error
    
    return response

# Enhanced comic generation with better error handling
def generate_comic_script_robust(input_text: str) -> dict:
    print("[Comic Generation] Starting robust comic script generation...")
    try:
        logger.info("Starting robust comic script generation")
        
        # Step 1: Generate characters and theme with retry logic
        characters_data = None
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                print(f"[Comic Generation] Step 1: Generating characters and theme (attempt {attempt + 1}/{max_retries})")
                logger.info(f"Step 1: Generating characters and theme (attempt {attempt + 1}/{max_retries})")
                characters_prompt = COMIC_CHARACTERS_PROMPT_TEMPLATE.format(input_text=input_text)
                characters_response = client.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=characters_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction="You are an expert comic scriptwriter. Always return valid JSON."
                    )
                )
                
                characters_text = None
                if characters_response:
                    if hasattr(characters_response, 'text') and characters_response.text:
                        characters_text = characters_response.text
                    elif (hasattr(characters_response, 'candidates') and 
                          characters_response.candidates and 
                          len(characters_response.candidates) > 0 and
                          hasattr(characters_response.candidates[0], 'content') and
                          characters_response.candidates[0].content and
                          hasattr(characters_response.candidates[0].content, 'parts') and
                          characters_response.candidates[0].content.parts and
                          len(characters_response.candidates[0].content.parts) > 0 and
                          hasattr(characters_response.candidates[0].content.parts[0], 'text')):
                        characters_text = characters_response.candidates[0].content.parts[0].text
                
                if not characters_text:
                    print("[Comic Generation] No text in characters model response or response is None.")
                    raise ValueError("No text in characters model response")
                
                characters_text = extract_json_from_response(characters_text)
                characters_data = json.loads(characters_text)
                print("[Comic Generation] Characters and theme generated:", characters_data)
                
                # Validate basic structure
                if not isinstance(characters_data, dict):
                    raise ValueError("Characters response is not a dictionary")
                
                if "character_style_guide" not in characters_data:
                    raise ValueError("Missing character_style_guide in response")
                
                logger.info("Successfully generated characters and theme")
                break
                
            except Exception as e:
                print(f"[Comic Generation] Attempt {attempt + 1} failed: {e}")
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2)  # Wait before retry
        
        # Step 2: Generate panels with retry logic
        panels_data = None
        
        for attempt in range(max_retries):
            try:
                print(f"[Comic Generation] Step 2: Generating panels (attempt {attempt + 1}/{max_retries})")
                logger.info(f"Step 2: Generating panels (attempt {attempt + 1}/{max_retries})")
                character_style_guide_str = json.dumps(characters_data.get('character_style_guide', {}))
                panels_prompt = COMIC_PANELS_PROMPT_TEMPLATE.format(
                    input_text=input_text,
                    character_style_guide=character_style_guide_str,
                    theme=characters_data.get('theme', 'Adventure')
                )
                
                panels_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=panels_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction="You are an expert comic scriptwriter. Generate 7-20 panels with meaningful dialogue. Always return valid JSON array."
                    )
                )
                
                panels_text = None
                if panels_response:
                    if hasattr(panels_response, 'text') and panels_response.text:
                        panels_text = panels_response.text
                    elif (hasattr(panels_response, 'candidates') and 
                          panels_response.candidates and 
                          len(panels_response.candidates) > 0 and
                          hasattr(panels_response.candidates[0], 'content') and
                          panels_response.candidates[0].content and
                          hasattr(panels_response.candidates[0].content, 'parts') and
                          panels_response.candidates[0].content.parts and
                          len(panels_response.candidates[0].content.parts) > 0 and
                          hasattr(panels_response.candidates[0].content.parts[0], 'text')):
                        panels_text = panels_response.candidates[0].content.parts[0].text
                
                if not panels_text:
                    print("[Comic Generation] No text in panels model response or response is None.")
                    raise ValueError("No text in panels model response")
                
                panels_text = extract_json_from_response(panels_text)
                
                # Try multiple parsing strategies
                try:
                    panels_data = json.loads(panels_text)
                    print("[Comic Generation] Panels generated:", panels_data)
                except json.JSONDecodeError:
                    print("[Comic Generation] Panels JSON decode error, trying to fix truncated JSON...")
                    fixed_panels_text = fix_truncated_panels_json(panels_text)
                    panels_data = json.loads(fixed_panels_text)
                    print("[Comic Generation] Panels generated after fixing:", panels_data)
                
                # Validate panels structure
                if not isinstance(panels_data, list):
                    raise ValueError("Panels response is not a list")
                
                if len(panels_data) < 3:
                    print(f"[Comic Generation] Too few panels generated: {len(panels_data)}")
                    raise ValueError(f"Too few panels generated: {len(panels_data)}")
                
                logger.info(f"Successfully generated {len(panels_data)} panels")
                break
                
            except Exception as e:
                print(f"[Comic Generation] Panel generation attempt {attempt + 1} failed: {e}")
                logger.error(f"Panel generation attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    # Create fallback panels
                    panels_data = create_fallback_panels("", characters_data.get('character_style_guide', {}))
                    print(f"[Comic Generation] Using {len(panels_data)} fallback panels")
                else:
                    time.sleep(2)  # Wait before retry
        
        # Combine and validate final comic data
        comic_data = {
            "comic_title": characters_data.get('comic_title', 'Generated Comic'),
            "theme": characters_data.get('theme', 'Adventure'),
            "character_style_guide": characters_data.get('character_style_guide', {}),
            "panel_layout": panels_data if isinstance(panels_data, list) else []
        }
        print("[Comic Generation] Final comic data ready for validation.")
        
        # Validate and sanitize the final comic data
        validated_comic = validate_comic_response(comic_data)
        print(f"[Comic Generation] Comic generation completed successfully with {len(validated_comic['panel_layout'])} panels.")
        return validated_comic
        
    except Exception as e:
        print(f"[Comic Generation] Comic script generation failed: {e}")
        logger.error(f"Comic script generation failed: {e}")
        # Return a safe fallback comic
        return {
            "comic_title": "Generated Comic",
            "theme": "Adventure",
            "character_style_guide": {"Character": "A brave adventurer"},
            "panel_layout": [
                {
                    "panel_id": 1,
                    "scene": "The adventure begins",
                    "image_prompt": "A character starting an adventure",
                    "dialogue": {"Character": "Let's begin our journey!"}
                }
            ]
        }

# Enhanced progress endpoint with better error handling
@app.route('/progress/<request_id>', methods=['GET'])
def get_progress(request_id):
    """Enhanced progress endpoint with better error handling"""
    try:
        progress = get_request_progress(request_id)
        if progress:
            return jsonify(create_frontend_compatible_response(
                success=True,
                data=progress,
                request_id=request_id
            )), 200
        else:
            return jsonify(create_frontend_compatible_response(
                success=False,
                error="Request not found",
                request_id=request_id
            )), 404
    except Exception as e:
        logger.error(f"Progress check failed for {request_id}: {e}")
        return jsonify(create_frontend_compatible_response(
            success=False,
            error="Failed to check progress",
            request_id=request_id
        )), 500

# Enhanced health check with comic-specific information
@app.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check with comic generation status"""
    try:
        memory_mb = get_memory_usage()
        
        # Check Google Cloud services status
        gcs_status = "unknown"
        tts_status = "unknown"
        
        try:
            if initialize_gcs():
                gcs_status = "healthy"
            else:
                gcs_status = "unhealthy"
        except Exception as e:
            gcs_status = f"error: {str(e)}"
        
        try:
            if initialize_tts():
                tts_status = "healthy"
            else:
                tts_status = "unhealthy"
        except Exception as e:
            tts_status = f"error: {str(e)}"
        
        # Check if comic generation is working
        comic_status = "healthy"
        try:
            # Test comic script generation with a simple input
            test_comic = generate_comic_script_robust("Test comic generation")
            if not test_comic or not test_comic.get('panel_layout'):
                comic_status = "unhealthy"
        except Exception as e:
            comic_status = f"error: {str(e)}"
        
        return jsonify(create_frontend_compatible_response(
            success=True,
            data={
                "status": "healthy",
                "memory_usage_mb": round(memory_mb, 2),
                "memory_warning": memory_mb > MEMORY_WARNING_MB,
                "memory_critical": memory_mb > MEMORY_LIMIT_MB,
                "google_cloud_services": {
                    "storage": gcs_status,
                    "text_to_speech": tts_status
                },
                "comic_generation": comic_status,
                "timestamp": datetime.now().isoformat()
            }
        )), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify(create_frontend_compatible_response(
            success=False,
            error=str(e)
        )), 500

# Main execution block for Cloud Run
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)



>>>>>>> 9129cfe4b41d693ce0501e8a686c17ac643b01c0

