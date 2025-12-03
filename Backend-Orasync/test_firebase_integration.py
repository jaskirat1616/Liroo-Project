#!/usr/bin/env python3
"""
Test script to verify Firebase integration in the backend
"""

import os
import sys
import json
from datetime import datetime

# Add the current directory to the path so we can import from backend.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import firebase_admin
    from firebase_admin import credentials, firestore, messaging
    print("✅ Firebase Admin SDK imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Firebase Admin SDK: {e}")
    sys.exit(1)

def test_firebase_initialization():
    """Test Firebase initialization"""
    try:
        # Try to initialize with service account key
        if os.path.exists("firebase-service-account.json"):
            cred = credentials.Certificate("firebase-service-account.json")
            firebase_admin.initialize_app(cred)
            print("✅ Firebase Admin SDK initialized with service account")
        else:
            # Try to initialize with default credentials
            firebase_admin.initialize_app()
            print("✅ Firebase Admin SDK initialized with default credentials")
        
        return True
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        return False

def test_firestore_connection():
    """Test Firestore connection"""
    try:
        db = firestore.client()
        print("✅ Firestore client initialized")
        
        # Test a simple write operation
        test_doc = db.collection('test').document('test_doc')
        test_doc.set({
            'test': True,
            'timestamp': datetime.now().isoformat(),
            'message': 'Firebase integration test'
        })
        print("✅ Firestore write test successful")
        
        # Test a simple read operation
        doc = test_doc.get()
        if doc.exists:
            print("✅ Firestore read test successful")
            # Clean up test document
            test_doc.delete()
            print("✅ Test document cleaned up")
        else:
            print("❌ Firestore read test failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Firestore test failed: {e}")
        return False

def test_messaging():
    """Test Firebase Messaging (without sending actual notification)"""
    try:
        # This is just a test to see if messaging is available
        # We won't actually send a notification in the test
        print("✅ Firebase Messaging module available")
        return True
    except Exception as e:
        print(f"❌ Firebase Messaging test failed: {e}")
        return False

def main():
    """Run all Firebase integration tests"""
    print("🧪 Testing Firebase Integration...")
    print("=" * 50)
    
    # Test 1: Firebase initialization
    if not test_firebase_initialization():
        print("❌ Firebase initialization test failed")
        return False
    
    # Test 2: Firestore connection
    if not test_firestore_connection():
        print("❌ Firestore connection test failed")
        return False
    
    # Test 3: Messaging availability
    if not test_messaging():
        print("❌ Firebase Messaging test failed")
        return False
    
    print("=" * 50)
    print("✅ All Firebase integration tests passed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 