#!/usr/bin/env python3
"""
Frontend-Backend Compatibility Test for Comic Generation
Tests that the backend response format matches exactly what the frontend expects
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
SERVER_HOST = 'liroo-backend-904791784838.us-central1.run.app'
BASE_URL = f'https://{SERVER_HOST}'

def test_frontend_compatibility():
    """Test that backend response matches frontend expectations"""
    print("🔍 Testing Frontend-Backend Compatibility")
    print("=" * 50)
    
    # Test payload that matches frontend format
    payload = {
        "text": "A cat discovers a computer and learns to use it. The cat becomes fascinated by the moving cursor and starts exploring the digital world.",
        "level": "moderate",
        "image_style": "Comic Book",
        "user_token": "test_token_123"
    }
    
    print(f"📤 Sending request to {BASE_URL}/generate_comic")
    print(f"📝 Text length: {len(payload['text'])} characters")
    print(f"📊 Level: {payload['level']}")
    print(f"🎨 Style: {payload['image_style']}")
    
    try:
        response = requests.post(f"{BASE_URL}/generate_comic", json=payload, timeout=300)
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        print(f"✅ Successfully received JSON response")
        
        # Test 1: Check response structure matches ComicResponse
        print("\n🔍 Test 1: Response Structure")
        required_fields = ['success', 'comic', 'request_id', 'timestamp']
        for field in required_fields:
            if field in data:
                print(f"   ✅ {field}: {type(data[field])} = {data[field]}")
            else:
                print(f"   ❌ Missing field: {field}")
                return False
        
        # Test 2: Check success flag
        print("\n🔍 Test 2: Success Flag")
        if data.get('success') == True:
            print("   ✅ success: true")
        else:
            print(f"   ❌ success: {data.get('success')}")
            return False
        
        # Test 3: Check comic data structure
        comic = data.get('comic')
        if not comic:
            print("   ❌ No comic data in response")
            return False
        
        print("\n🔍 Test 3: Comic Data Structure")
        comic_fields = ['comic_title', 'theme', 'character_style_guide', 'panel_layout']
        for field in comic_fields:
            if field in comic:
                print(f"   ✅ {field}: {type(comic[field])}")
            else:
                print(f"   ❌ Missing comic field: {field}")
                return False
        
        # Test 4: Check character style guide format (MUST be string values)
        print("\n🔍 Test 4: Character Style Guide Format")
        style_guide = comic.get('character_style_guide', {})
        if not isinstance(style_guide, dict):
            print(f"   ❌ character_style_guide is not a dict: {type(style_guide)}")
            return False
        
        print(f"   📊 Found {len(style_guide)} characters")
        for char_name, description in style_guide.items():
            if isinstance(description, str):
                print(f"   ✅ {char_name}: {description[:50]}...")
            else:
                print(f"   ❌ {char_name}: {type(description)} = {description}")
                print("   💡 Character descriptions must be strings, not dictionaries")
                return False
        
        # Test 5: Check panel layout structure
        print("\n🔍 Test 5: Panel Layout Structure")
        panels = comic.get('panel_layout', [])
        if not isinstance(panels, list):
            print(f"   ❌ panel_layout is not a list: {type(panels)}")
            return False
        
        print(f"   📊 Found {len(panels)} panels")
        if len(panels) < 3:
            print(f"   ⚠️  Warning: Only {len(panels)} panels (minimum 3 recommended)")
        
        required_panel_fields = ['panel_id', 'scene', 'image_prompt', 'dialogue']
        for i, panel in enumerate(panels):
            print(f"   📋 Panel {i+1}:")
            for field in required_panel_fields:
                if field in panel:
                    value = panel[field]
                    if field == 'dialogue':
                        if isinstance(value, dict):
                            print(f"      ✅ {field}: {len(value)} dialogue entries")
                            for char, text in value.items():
                                if isinstance(text, str):
                                    print(f"         ✅ {char}: {text[:30]}...")
                                else:
                                    print(f"         ❌ {char}: {type(text)} = {text}")
                                    return False
                        else:
                            print(f"      ❌ {field}: {type(value)} (must be dict)")
                            return False
                    else:
                        if isinstance(value, str):
                            print(f"      ✅ {field}: {value[:50]}...")
                        else:
                            print(f"      ❌ {field}: {type(value)} = {value}")
                            return False
                else:
                    print(f"      ❌ Missing panel field: {field}")
                    return False
            
            # Check for image_url (optional)
            if 'image_url' in panel and panel['image_url']:
                print(f"      ✅ image_url: {panel['image_url'][:50]}...")
            else:
                print(f"      ⚠️  No image_url (may still be generating)")
        
        # Test 6: Validate JSON serialization (frontend compatibility)
        print("\n🔍 Test 6: JSON Serialization")
        try:
            # Simulate frontend decoding
            json_str = json.dumps(data)
            decoded_data = json.loads(json_str)
            print("   ✅ JSON serialization/deserialization successful")
            
            # Test ComicResponse structure
            if 'success' in decoded_data and 'comic' in decoded_data:
                print("   ✅ ComicResponse structure valid")
            else:
                print("   ❌ ComicResponse structure invalid")
                return False
                
        except Exception as e:
            print(f"   ❌ JSON serialization failed: {e}")
            return False
        
        # Test 7: Check data types match frontend expectations
        print("\n🔍 Test 7: Data Type Validation")
        
        # Comic title should be string
        if isinstance(comic.get('comic_title'), str):
            print("   ✅ comic_title: string")
        else:
            print(f"   ❌ comic_title: {type(comic.get('comic_title'))}")
            return False
        
        # Theme should be string
        if isinstance(comic.get('theme'), str):
            print("   ✅ theme: string")
        else:
            print(f"   ❌ theme: {type(comic.get('theme'))}")
            return False
        
        # Panel ID should be integer
        for i, panel in enumerate(panels):
            if isinstance(panel.get('panel_id'), int):
                print(f"   ✅ panel {i+1} panel_id: int")
            else:
                print(f"   ❌ panel {i+1} panel_id: {type(panel.get('panel_id'))}")
                return False
        
        print("\n🎉 All Frontend-Backend Compatibility Tests Passed!")
        print("✅ Backend response format is fully compatible with frontend expectations")
        return True
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_error_handling():
    """Test error handling scenarios"""
    print("\n🔍 Testing Error Handling")
    print("=" * 30)
    
    # Test 1: Empty text
    print("📝 Test: Empty text")
    payload = {"text": "", "level": "moderate", "image_style": "Comic Book"}
    response = requests.post(f"{BASE_URL}/generate_comic", json=payload)
    if response.status_code == 400:
        print("   ✅ Correctly rejected empty text")
    else:
        print(f"   ❌ Expected 400, got {response.status_code}")
    
    # Test 2: Invalid level
    print("📝 Test: Invalid level")
    payload = {"text": "Test comic", "level": "invalid", "image_style": "Comic Book"}
    response = requests.post(f"{BASE_URL}/generate_comic", json=payload)
    if response.status_code == 200:  # Should still work with fallback
        print("   ✅ Handled invalid level gracefully")
    else:
        print(f"   ❌ Unexpected response: {response.status_code}")
    
    # Test 3: Missing required fields
    print("📝 Test: Missing text field")
    payload = {"level": "moderate", "image_style": "Comic Book"}
    response = requests.post(f"{BASE_URL}/generate_comic", json=payload)
    if response.status_code == 400:
        print("   ✅ Correctly rejected missing text")
    else:
        print(f"   ❌ Expected 400, got {response.status_code}")

def main():
    """Run all compatibility tests"""
    print("🚀 Frontend-Backend Comic Generation Compatibility Test")
    print("=" * 60)
    
    # Test basic compatibility
    success = test_frontend_compatibility()
    
    # Test error handling
    test_error_handling()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        print("✅ Backend is fully compatible with frontend expectations")
        return 0
    else:
        print("\n❌ Some tests failed!")
        print("🔧 Backend needs fixes for frontend compatibility")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 