# Simple test script to check comic dialogue generation
import requests
import json

# Configuration
API_URL = 'https://liroo-backend-904791784838.us-central1.run.app/generate_comic'

payload = {
    "text": "A simple test story about a cat learning to use a computer.",
    "level": "moderate",
    "image_style": "Comic Book"
}

print(f"Sending request to {API_URL}...")
resp = requests.post(API_URL, json=payload)
if resp.status_code != 200:
    print(f"Error: {resp.status_code}", resp.text)
    exit(1)

data = resp.json()
comic = data.get('comic')
if not comic:
    print("No comic in response.")
    exit(1)

panels = comic.get('panel_layout', [])
if not panels:
    print("No panels found in comic.")
    exit(1)

print(f"\nComic title: {comic.get('comic_title')}")
print(f"Theme: {comic.get('theme')}")
print(f"Total panels generated: {len(panels)}")

print("\n=== DIALOGUE ANALYSIS ===")
for i, panel in enumerate(panels, 1):
    print(f"\nPanel {i}:")
    print(f"  Scene: {panel.get('scene', 'N/A')}")
    print(f"  Dialogue: {panel.get('dialogue', {})}")
    
    # Check if dialogue is meaningful
    dialogue = panel.get('dialogue', {})
    if dialogue:
        for character, text in dialogue.items():
            if "Panel" in text and "dialogue" in text:
                print(f"    ❌ Generic dialogue detected: '{text}'")
            else:
                print(f"    ✅ Meaningful dialogue: '{text}'")
    else:
        print(f"    ❌ No dialogue found")

print(f"\n=== SUMMARY ===")
print(f"Generated {len(panels)} panels")
print("Check the dialogue quality above.") 