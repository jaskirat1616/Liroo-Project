#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

def test_imports():
    """Test all required imports"""
    try:
        print("Testing imports...")
        
        # Test Flask imports
        from flask import Flask, request, jsonify
        from flask_cors import CORS
        print("✅ Flask imports successful")
        
        # Test Google GenAI imports
        import google.generativeai as genai
        print("✅ Google GenAI imports successful")
        
        # Test Google Cloud imports
        from google.cloud import storage
        from google.cloud import texttospeech
        print("✅ Google Cloud imports successful")
        
        # Test PIL imports
        from PIL import Image, ImageDraw, ImageFont
        print("✅ PIL imports successful")
        
        # Test other imports
        from dotenv import load_dotenv
        import datetime
        import hashlib
        import uuid
        import time
        import threading
        from datetime import datetime, timedelta
        print("✅ Standard library imports successful")
        
        # Test Firebase imports
        import firebase_admin
        from firebase_admin import credentials, firestore, messaging
        print("✅ Firebase Admin imports successful")
        
        print("✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1) 