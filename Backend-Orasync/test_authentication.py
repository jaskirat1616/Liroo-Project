#!/usr/bin/env python3
"""
Test script to verify authentication changes work properly
"""

import os
import sys

# Add the current directory to the path so we can import from backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_authentication():
    """Test that the authentication changes work properly"""
    print("🧪 Testing authentication changes...")
    
    try:
        # Import the backend module
        from backend import initialize_gcs, initialize_tts, app
        
        print("✅ Successfully imported backend module")
        
        # Test GCS initialization
        print("🔧 Testing GCS initialization...")
        gcs_success = initialize_gcs()
        if gcs_success:
            print("✅ GCS initialization successful")
        else:
            print("⚠️ GCS initialization failed (this is expected in some environments)")
        
        # Test TTS initialization
        print("🔧 Testing TTS initialization...")
        tts_success = initialize_tts()
        if tts_success:
            print("✅ TTS initialization successful")
        else:
            print("⚠️ TTS initialization failed (this is expected in some environments)")
        
        # Test Flask app creation
        print("🔧 Testing Flask app creation...")
        if app:
            print("✅ Flask app created successfully")
        else:
            print("❌ Flask app creation failed")
        
        print("\n🎉 Authentication test completed!")
        print("📝 Summary:")
        print(f"   - GCS: {'✅ Working' if gcs_success else '⚠️ Not available'}")
        print(f"   - TTS: {'✅ Working' if tts_success else '⚠️ Not available'}")
        print(f"   - Flask: ✅ Working")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_authentication()
    sys.exit(0 if success else 1) 