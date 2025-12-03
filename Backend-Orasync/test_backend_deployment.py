#!/usr/bin/env python3
"""
Simple test script to verify backend deployment
"""

import requests
import json
import sys

# Configuration
SERVER_HOST = 'liroo-backend-904791784838.us-central1.run.app'
BASE_URL = f'https://{SERVER_HOST}'

def test_backend_deployment():
    """Test basic backend functionality"""
    print("🔍 Testing Backend Deployment")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Health check passed")
            print(f"   Status: {data.get('data', {}).get('status', 'unknown')}")
            print(f"   Memory: {data.get('data', {}).get('memory_usage_mb', 'unknown')} MB")
            print(f"   Comic Generation: {data.get('data', {}).get('comic_generation', 'unknown')}")
        else:
            print(f"   ❌ Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test 2: Basic endpoint
    print("\n2. Testing basic endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Basic endpoint working")
            print(f"   Message: {data.get('message', 'unknown')}")
        else:
            print(f"   ❌ Basic endpoint failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Basic endpoint error: {e}")
        return False
    
    # Test 3: Test API endpoint
    print("\n3. Testing test API endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/test-api", timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Test API working")
            print(f"   Message: {data.get('message', 'unknown')}")
        else:
            print(f"   ❌ Test API failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Test API error: {e}")
        return False
    
    print("\n✅ All basic tests passed! Backend is deployed and working.")
    return True

def test_comic_endpoint():
    """Test comic generation endpoint"""
    print("\n🎨 Testing Comic Generation Endpoint")
    print("=" * 50)
    
    payload = {
        "text": "A cat discovers a computer and learns to use it. The cat becomes fascinated by the screen and starts typing.",
        "level": "moderate",
        "image_style": "Comic Book"
    }
    
    try:
        print("Sending comic generation request...")
        response = requests.post(f"{BASE_URL}/generate_comic", json=payload, timeout=120)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Comic generation successful!")
            print(f"Success: {data.get('success', False)}")
            
            if data.get('success') and 'data' in data and 'comic' in data['data']:
                comic = data['data']['comic']
                print(f"Comic Title: {comic.get('comic_title', 'Unknown')}")
                print(f"Theme: {comic.get('theme', 'Unknown')}")
                print(f"Panels: {len(comic.get('panel_layout', []))}")
                print(f"Characters: {len(comic.get('character_style_guide', {}))}")
                return True
            else:
                print(f"❌ Comic generation failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Comic generation failed with status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Comic generation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Backend Deployment Test Suite")
    print("=" * 60)
    
    # Test basic deployment
    if not test_backend_deployment():
        print("\n❌ Basic deployment tests failed!")
        sys.exit(1)
    
    # Test comic generation
    if not test_comic_endpoint():
        print("\n❌ Comic generation test failed!")
        sys.exit(1)
    
    print("\n🎉 All tests passed! Backend is fully operational.")
    print("Frontend should now be able to connect successfully.")

if __name__ == "__main__":
    main() 