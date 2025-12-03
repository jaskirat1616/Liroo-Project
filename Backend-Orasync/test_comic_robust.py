#!/usr/bin/env python3
"""
Comprehensive test script for enhanced comic generation backend
Tests various edge cases, error conditions, and response formats
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
SERVER_HOST = 'liroo-backend-904791784838.us-central1.run.app'
BASE_URL = f'https://{SERVER_HOST}'

def test_health_check():
    """Test the enhanced health check endpoint"""
    print("🔍 Testing health check endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check successful")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Memory Usage: {data.get('memory_usage_mb', 'unknown')} MB")
            print(f"   Comic Generation: {data.get('comic_generation', 'unknown')}")
            print(f"   Success: {data.get('success', 'unknown')}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_comic_generation_basic():
    """Test basic comic generation with valid input"""
    print("\n🎨 Testing basic comic generation...")
    
    payload = {
        "text": "A cat learns to use a computer and discovers the internet.",
        "level": "moderate",
        "image_style": "Comic Book",
        "user_token": "test_token_123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generate_comic", json=payload, timeout=300)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Comic generation successful")
            print(f"   Success: {data.get('success', 'unknown')}")
            print(f"   Request ID: {data.get('request_id', 'none')}")
            print(f"   Timestamp: {data.get('timestamp', 'none')}")
            
            if 'comic' in data:
                comic = data['comic']
                print(f"   Comic Title: {comic.get('comic_title', 'unknown')}")
                print(f"   Theme: {comic.get('theme', 'unknown')}")
                print(f"   Characters: {len(comic.get('character_style_guide', {}))}")
                print(f"   Panels: {len(comic.get('panel_layout', []))}")
                
                # Validate character style guide format
                style_guide = comic.get('character_style_guide', {})
                for char_name, description in style_guide.items():
                    if not isinstance(description, str):
                        print(f"   ⚠️  Character '{char_name}' has non-string description: {type(description)}")
                    else:
                        print(f"   ✅ Character '{char_name}': {description[:50]}...")
                
                # Validate panel structure
                panels = comic.get('panel_layout', [])
                for i, panel in enumerate(panels):
                    required_fields = ['panel_id', 'scene', 'image_prompt', 'dialogue']
                    for field in required_fields:
                        if field not in panel:
                            print(f"   ❌ Panel {i} missing required field: {field}")
                        elif field == 'dialogue' and not isinstance(panel[field], dict):
                            print(f"   ❌ Panel {i} dialogue is not a dictionary: {type(panel[field])}")
                        elif field == 'dialogue' and not panel[field]:
                            print(f"   ⚠️  Panel {i} has empty dialogue")
                        else:
                            print(f"   ✅ Panel {i} {field}: {str(panel[field])[:50]}...")
            
            return True
        else:
            print(f"❌ Comic generation failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Comic generation error: {e}")
        return False

def test_comic_generation_edge_cases():
    """Test comic generation with edge cases"""
    print("\n🧪 Testing edge cases...")
    
    test_cases = [
        {
            "name": "Empty text",
            "payload": {"text": "", "level": "moderate", "image_style": "Comic Book"},
            "expected_status": 400
        },
        {
            "name": "Very long text",
            "payload": {"text": "A" * 6000, "level": "moderate", "image_style": "Comic Book"},
            "expected_status": 400
        },
        {
            "name": "Missing text",
            "payload": {"level": "moderate", "image_style": "Comic Book"},
            "expected_status": 400
        },
        {
            "name": "Invalid level",
            "payload": {"text": "Test story", "level": "invalid_level", "image_style": "Comic Book"},
            "expected_status": 200  # Should still work with fallback
        }
    ]
    
    for test_case in test_cases:
        print(f"   Testing: {test_case['name']}")
        try:
            response = requests.post(f"{BASE_URL}/generate_comic", json=test_case['payload'], timeout=60)
            if response.status_code == test_case['expected_status']:
                print(f"   ✅ Expected status {test_case['expected_status']}, got {response.status_code}")
            else:
                print(f"   ⚠️  Expected status {test_case['expected_status']}, got {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') == False:
                        print(f"   ✅ Backend properly indicated failure")
                    else:
                        print(f"   ⚠️  Backend returned success despite invalid input")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_progress_polling():
    """Test progress polling functionality"""
    print("\n📊 Testing progress polling...")
    
    # First generate a comic to get a request ID
    payload = {
        "text": "A quick test story about a robot learning to paint.",
        "level": "moderate",
        "image_style": "Comic Book"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generate_comic", json=payload, timeout=300)
        if response.status_code == 200:
            data = response.json()
            request_id = data.get('request_id')
            
            if request_id:
                print(f"   Got request ID: {request_id}")
                
                # Test progress polling
                progress_response = requests.get(f"{BASE_URL}/progress/{request_id}", timeout=30)
                if progress_response.status_code == 200:
                    progress_data = progress_response.json()
                    print(f"   ✅ Progress polling successful")
                    print(f"   Success: {progress_data.get('success', 'unknown')}")
                    print(f"   Step: {progress_data.get('step', 'unknown')}")
                    print(f"   Progress: {progress_data.get('progress_percentage', 'unknown')}%")
                else:
                    print(f"   ❌ Progress polling failed: {progress_response.status_code}")
            else:
                print("   ⚠️  No request ID returned")
        else:
            print(f"   ❌ Comic generation failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Progress polling error: {e}")

def test_response_format_validation():
    """Test that responses are in the expected format"""
    print("\n🔍 Testing response format validation...")
    
    payload = {
        "text": "A simple test story for format validation.",
        "level": "moderate",
        "image_style": "Comic Book"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generate_comic", json=payload, timeout=300)
        if response.status_code == 200:
            data = response.json()
            
            # Check for new standardized response format
            required_fields = ['success', 'timestamp']
            for field in required_fields:
                if field in data:
                    print(f"   ✅ Response contains '{field}': {data[field]}")
                else:
                    print(f"   ❌ Response missing '{field}'")
            
            # Validate comic structure if present
            if 'comic' in data and data['comic']:
                comic = data['comic']
                comic_fields = ['comic_title', 'theme', 'character_style_guide', 'panel_layout']
                for field in comic_fields:
                    if field in comic:
                        print(f"   ✅ Comic contains '{field}'")
                    else:
                        print(f"   ❌ Comic missing '{field}'")
            
            # Check for request_id
            if 'request_id' in data:
                print(f"   ✅ Response contains request_id: {data['request_id']}")
            else:
                print(f"   ⚠️  Response missing request_id")
                
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Format validation error: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting comprehensive comic generation backend tests")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health_check),
        ("Basic Comic Generation", test_comic_generation_basic),
        ("Edge Cases", test_comic_generation_edge_cases),
        ("Progress Polling", test_progress_polling),
        ("Response Format Validation", test_response_format_validation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Backend is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 