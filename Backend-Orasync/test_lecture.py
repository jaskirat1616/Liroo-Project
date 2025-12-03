#!/usr/bin/env python3
"""
Test script for the new lecture generation functionality.
This script demonstrates how to use the /generate_lecture endpoint.
"""

import requests
import json
import os
from datetime import datetime

# Configuration
<<<<<<< HEAD
BASE_URL = "https://backend-orasync-test.onrender.com"  # Change this to your backend URL
=======
BASE_URL = "http://127.0.0.1:5001"  # Change this to your backend URL
>>>>>>> 9129cfe4b41d693ce0501e8a686c17ac643b01c0

def save_lecture_data(result, output_dir="lecture_output"):
    """Save lecture data to local files."""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save full response as JSON
    full_response_file = os.path.join(output_dir, f"lecture_response_{timestamp}.json")
    with open(full_response_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"📄 Full response saved to: {full_response_file}")
    
    # Save lecture content as readable text
    lecture = result.get('lecture', {})
    lecture_text_file = os.path.join(output_dir, f"lecture_content_{timestamp}.txt")
    
    with open(lecture_text_file, 'w', encoding='utf-8') as f:
        f.write(f"LECTURE: {lecture.get('title', 'Untitled')}\n")
        f.write("=" * 50 + "\n\n")
        
        sections = lecture.get('sections', [])
        for i, section in enumerate(sections, 1):
            f.write(f"SECTION {i}: {section.get('title', 'Untitled')}\n")
            f.write("-" * 30 + "\n")
            f.write(f"Script:\n{section.get('script', 'No script available')}\n\n")
            f.write(f"Image Prompt:\n{section.get('image_prompt', 'No image prompt')}\n")
            if section.get('image_url'):
                f.write(f"Image URL: {section.get('image_url')}\n")
            f.write("\n" + "=" * 50 + "\n\n")
    
    print(f"📝 Lecture content saved to: {lecture_text_file}")
    
    # Save audio file information
    audio_files = result.get('audio_files', [])
    if audio_files:
        audio_info_file = os.path.join(output_dir, f"audio_files_{timestamp}.txt")
        with open(audio_info_file, 'w', encoding='utf-8') as f:
            f.write("AUDIO FILES GENERATED:\n")
            f.write("=" * 30 + "\n\n")
            
            for audio in audio_files:
                audio_type = audio.get('type', 'unknown')
                section_num = audio.get('section', 'N/A')
                filename = audio.get('filename', 'N/A')
                url = audio.get('url', 'N/A')
                text = audio.get('text', 'N/A')
                
                f.write(f"Type: {audio_type}\n")
                f.write(f"Section: {section_num}\n")
                f.write(f"Filename: {filename}\n")
                f.write(f"Text: {text}\n")
                f.write(f"URL: {url}\n")
                f.write("-" * 20 + "\n\n")
        
        print(f"🎵 Audio file info saved to: {audio_info_file}")
    
    # Save URLs for easy access
    urls_file = os.path.join(output_dir, f"lecture_urls_{timestamp}.txt")
    with open(urls_file, 'w', encoding='utf-8') as f:
        f.write("LECTURE RESOURCES:\n")
        f.write("=" * 20 + "\n\n")
        
        # Image URLs
        f.write("IMAGES:\n")
        sections = lecture.get('sections', [])
        for i, section in enumerate(sections, 1):
            if section.get('image_url'):
                f.write(f"Section {i}: {section.get('image_url')}\n")
        f.write("\n")
        
        # Audio URLs
        f.write("AUDIO FILES:\n")
        for audio in audio_files:
            audio_type = audio.get('type', 'unknown')
            section_num = audio.get('section', 'N/A')
            f.write(f"{audio_type} (Section {section_num}): {audio.get('url', 'N/A')}\n")
    
    print(f"🔗 URLs saved to: {urls_file}")
    
    return {
        'full_response': full_response_file,
        'lecture_content': lecture_text_file,
        'audio_info': audio_info_file if audio_files else None,
        'urls': urls_file
    }

def test_lecture_generation():
    """Test the lecture generation endpoint."""
    
    # Sample text for lecture generation
    sample_text = """
    The creation of 3D assets, encompassing characters, props, and intricate environments, remains a time-intensive and technically demanding endeavor within the realms of video game development, augmented and virtual reality experiences, and special effects in filmmaking. This process traditionally necessitates a high level of artistic skill and technical expertise, often proving to be a bottleneck in content creation pipelines.

    Recognizing this challenge, Meta 3D Gen emerges as a potential game-changer, empowering creators with an AI-powered assistant capable of rapidly generating high-fidelity 3D assets from simple text prompts. This transformative technology holds the potential to democratize 3D content creation, opening up new avenues for personalized user-generated experiences and fueling the development of immersive virtual worlds within the metaverse.
    """
    
    # Prepare the request payload
    payload = {
        "text": sample_text,
<<<<<<< HEAD
        "level": "Teen",  # Can be: Kid, PreTeen, Teen, University, Standard
=======
        "level": "moderate",  # Can be: beginner, moderate, intermediate
>>>>>>> 9129cfe4b41d693ce0501e8a686c17ac643b01c0
        "image_style": "Studio Ghibli"  # Optional: can be Studio Ghibli, Educational, Disney Classic, etc.
    }
    
    print("🚀 Testing lecture generation...")
    print(f"📝 Input text length: {len(sample_text)} characters")
    print(f"📚 Reading level: {payload['level']}")
    print(f"🎨 Image style: {payload['image_style']}")
    print("-" * 50)
    
    try:
        # Make the request
        response = requests.post(
            f"{BASE_URL}/generate_lecture",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Lecture generation successful!")
            print(f"📋 Lecture ID: {result.get('lecture_id', 'N/A')}")
            
            # Display lecture data
            lecture = result.get('lecture', {})
            print(f"📖 Title: {lecture.get('title', 'N/A')}")
            
            # Display sections
            sections = lecture.get('sections', [])
            print(f"📚 Number of sections: {len(sections)}")
            
            for i, section in enumerate(sections, 1):
                print(f"\n--- Section {i} ---")
                print(f"📝 Title: {section.get('title', 'N/A')}")
                print(f"🎙️ Script length: {len(section.get('script', ''))} characters")
                print(f"🖼️ Has image: {'Yes' if section.get('image_url') else 'No'}")
            
            # Display audio files
            audio_files = result.get('audio_files', [])
            print(f"\n🎵 Number of audio files: {len(audio_files)}")
            
            for audio in audio_files:
                audio_type = audio.get('type', 'unknown')
                section_num = audio.get('section', 'N/A')
                print(f"  - {audio_type} (Section {section_num}): {audio.get('filename', 'N/A')}")
            
            # Save data locally
            print("\n💾 Saving lecture data locally...")
            saved_files = save_lecture_data(result)
            
            print("\n📁 Files saved:")
            for file_type, file_path in saved_files.items():
                if file_path:
                    print(f"  - {file_type}: {file_path}")
            
            print("\n🎉 Test completed successfully!")
            print(f"📂 Check the 'lecture_output' folder for all generated files!")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Save error response
            error_file = f"lecture_output/error_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            os.makedirs("lecture_output", exist_ok=True)
            with open(error_file, 'w') as f:
                f.write(f"Status Code: {response.status_code}\n")
                f.write(f"Response: {response.text}\n")
            print(f"📄 Error response saved to: {error_file}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the backend server is running on", BASE_URL)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_backend_health():
    """Test if the backend is running."""
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Backend is running!")
            return True
        else:
            print(f"❌ Backend responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running or not accessible")
        return False

if __name__ == "__main__":
    print("🧪 Lecture Generation Test Script")
    print("=" * 50)
    
    # First check if backend is running
    if test_backend_health():
        print()
        test_lecture_generation()
    else:
        print("\n💡 To start the backend, run:")
        print("   python backend.py")
        print("\n💡 Make sure you have:")
        print("   1. Set up Google Cloud credentials (GOOGLE_APPLICATION_CREDENTIALS)")
        print("   2. Installed all dependencies: pip install -r requirements.txt")
        print("   3. Set up your .env file with GENAI_API_KEY and GCS_BUCKET_NAME")