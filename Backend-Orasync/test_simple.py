#!/usr/bin/env python3
import requests
import json

# Test the backend step by step
BASE_URL = "https://liroo-backend-904791784838.us-central1.run.app"

def test_endpoint(endpoint, method="GET", data=None):
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🔍 Testing: {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=120)
        else:
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=data, headers=headers, timeout=120)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ Success: {json.dumps(result, indent=2)[:200]}...")
                return True
            except:
                print(f"✅ Success: {response.text[:200]}...")
                return True
        else:
            print(f"❌ Error: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

# Test basic endpoints
print("🚀 Testing Backend Endpoints")
print("=" * 50)

test_endpoint("/")
test_endpoint("/health")
test_endpoint("/test-api")

# Test simple process request
simple_data = {
    "input_text": "The sun is bright today.",
    "level": "moderate"
}
test_endpoint("/process", "POST", simple_data)

print("\n✅ Testing complete!") 