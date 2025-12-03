# Test script for /generate_comic endpoint
# Requirements: requests, opencv-python
# Install with: pip install requests opencv-python

import requests
import cv2
import numpy as np
import time
import os

# Configuration
SERVER_HOST = 'liroo-backend-904791784838.us-central1.run.app'
SERVER_PORT = '443'  # Cloud Run uses HTTPS on port 443
API_URL = f'https://{SERVER_HOST}/generate_comic'
BASE_URL = f'https://{SERVER_HOST}'

payload = {
    "text": """The internal cameras and sensors scan the eye movement to know which direction the pupils are moving.
The external cameras scan the environment and sense where the phone is in space through parallax.
This array of cameras and sensors allow the glasses to track where your eyes are looking on the phone instantly and accurately
The widget used to navigate around the phone is similar to the mouse design on the iPad. This keeps the design language without compromising with user experience.""",
    "level": "intermediate",
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

print(f"Comic title: {comic.get('comic_title')}")
print(f"Theme: {comic.get('theme')}")
print(f"Character Style Guide: {comic.get('character_style_guide')}")
print(f"Total panels generated: {len(panels)}")

# Create output directory for saved images
output_dir = "comic_output"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"Created output directory: {output_dir}")

for panel in panels:
    print(f"\nPanel {panel.get('panel_id')}: {panel.get('scene')}")
    print(f"Dialogue: {panel.get('dialogue')}")
    
    img_url = panel.get('image_url')
    if not img_url:
        print("No image URL for this panel.")
        continue
    
    # Construct full URL
    if img_url.startswith('/'):
        full_img_url = BASE_URL + img_url
    else:
        full_img_url = img_url
    
    print(f"Downloading image: {full_img_url}")
    
    try:
        img_resp = requests.get(full_img_url)
        img_resp.raise_for_status()
        
        # Convert response content to image
        img_array = np.asarray(bytearray(img_resp.content), dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if img is None:
            print("Failed to decode image.")
            continue
            
        # Display dialogue at the bottom (not scene text)
        dialogue = panel.get('dialogue', {})
        if dialogue:
            # Prepare black strip at the bottom
            h, w = img.shape[:2]
            strip_height = 80  # Increased height for dialogue
            overlay = img.copy()
            cv2.rectangle(overlay, (0, h - strip_height), (w, h), (0, 0, 0), -1)
            alpha = 0.8
            img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
            
            # Put dialogue text (wrap if too long)
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            font_thickness = 1
            text_color = (255, 255, 255)
            margin = 15
            max_text_width = w - 2 * margin
            
            # Format dialogue text
            dialogue_lines = []
            for character, text in dialogue.items():
                dialogue_lines.append(f"{character}: {text}")
            
            dialogue_text = " | ".join(dialogue_lines)
            
            # Simple wrap: split if too long
            text_size, _ = cv2.getTextSize(dialogue_text, font, font_scale, font_thickness)
            if text_size[0] > max_text_width:
                # Split into multiple lines
                words = dialogue_text.split()
                lines = []
                current_line = ""
                for word in words:
                    test_line = current_line + (' ' if current_line else '') + word
                    if cv2.getTextSize(test_line, font, font_scale, font_thickness)[0][0] < max_text_width:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)
                
                # Display multiple lines
                y0 = h - strip_height + 25
                for i, line in enumerate(lines[:3]):  # Limit to 3 lines
                    cv2.putText(img, line, (margin, y0 + i * 20), font, font_scale, text_color, font_thickness, cv2.LINE_AA)
            else:
                y = h - strip_height//2 + 10
                cv2.putText(img, dialogue_text, (margin, y), font, font_scale, text_color, font_thickness, cv2.LINE_AA)
        
        # Save image locally
        filename = os.path.join(output_dir, f"panel_{panel.get('panel_id')}.png")
        cv2.imwrite(filename, img)
        print(f"Saved image as {filename}")
        
        # Display image
        window_name = f"Panel {panel.get('panel_id')}"
        cv2.imshow(window_name, img)
        print("Press any key to continue to next panel...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        time.sleep(0.5)
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
    except Exception as e:
        print(f"Error processing image: {e}")

print(f"\nDone! All images saved in '{output_dir}' directory.")
print(f"Generated {len(panels)} panels with dialogues.") 