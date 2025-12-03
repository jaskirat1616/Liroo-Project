<div align="center">
  <img src="Liroo/Resources/Assets.xcassets/AppIcon.appiconset/High%20Res%20Character%20Image%20Jul%204%202025.png" alt="Liroo App Icon" width="200" height="200">
  
  # Liroo
  
  **AI-powered content generation platform for creating accessible, engaging educational content**
  
  [![Swift](https://img.shields.io/badge/Swift-5.9-orange.svg)](https://swift.org)
  [![iOS](https://img.shields.io/badge/iOS-15.0+-blue.svg)](https://developer.apple.com/ios/)
  [![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
</div>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

## Overview

Liroo is an iOS application that transforms text into engaging, accessible content using AI. It generates stories, lectures, comics, and educational content tailored to different reading levels, with features like text-to-speech narration and dyslexia-friendly formatting.

The platform is designed to make learning more accessible, especially for users with dyslexia and younger audiences, by adapting content complexity and providing multiple engagement formats.

## Features

### Content Generation

- **Story Generation**: Create engaging stories with customizable genres (Adventure, Fantasy, Mystery, Science Fiction, Historical, Educational), main characters, and reading levels
- **Lecture Generation**: Generate educational lectures with audio narration, visual content, and structured sections
- **Comic Generation**: Create multi-panel comics with character dialogue, original artwork, and narrative flow
- **Content Adaptation**: Transform any text to match reading levels (beginner to advanced) with appropriate vocabulary and sentence structure
- **Detailed Explanations**: Generate comprehensive explanations with quizzes, examples, and visual aids

### Text-to-Speech (The Narrator)

- **Built-in TTS**: Uses Gemini 2.5 Flash Preview TTS model for natural narration
- **Friendly Voice**: Warm, engaging narrator voice optimized for storytelling
- **Seamless Playback**: Automatic audio management with play/pause/stop controls
- **Background Playback**: Audio continues playing when app is in background
- **Bedtime Story Experience**: Designed to read like a parent reading a bedtime story

### User Interface

- **Glass Morphism Design**: Modern, translucent UI with depth and visual clarity
- **Responsive Layout**: Optimized for both iPhone and iPad with adaptive layouts
- **Dark Mode**: Full support for light and dark appearances with theme customization
- **Accessibility**: Dyslexia-friendly fonts (OpenDyslexic), customizable font sizes, and reading themes
- **Smooth Animations**: Polished transitions and interactions throughout the app

### Additional Capabilities

- **OCR Integration**: Extract text from images using camera or photo library with Vision framework
- **File Import**: Support for PDFs and image files with multi-page processing
- **History Management**: Track and access previously generated content with search and filtering
- **Background Processing**: Content generation continues even when app is in background
- **Progress Tracking**: Real-time progress updates for long-running generation tasks
- **Interactive Dialogue**: Ask questions about content and get AI-powered responses
- **User Profiles**: Personalized experience with user accounts and preferences

## Architecture

### Technology Stack

**Frontend (iOS)**
- **SwiftUI**: Modern declarative UI framework
- **Firebase**: Authentication, Firestore database, Cloud Storage, Analytics, Crashlytics
- **AVFoundation**: Audio playback for TTS and lecture narration
- **Vision Framework**: OCR for text extraction from images
- **Combine**: Reactive programming for data flow
- **Swift Package Manager**: Dependency management

**Backend**
- **Flask**: Python web framework for API services
- **Google Gemini**: AI models for content generation (2.5 Flash, 3.0 Pro Exp)
- **Google Cloud Storage**: Asset storage for generated images and audio
- **Google Cloud Text-to-Speech**: TTS synthesis
- **Cloud Run**: Serverless deployment platform (recommended)

### Project Structure

This is a **single repository** containing both the iOS app and backend:

```
Liroo-Project/
├── Liroo/                    # iOS Application Source Code
│   ├── Application/         # App entry point and coordination
│   │   ├── LirooApp.swift
│   │   ├── AppCoordinator.swift
│   │   ├── MainTabView.swift
│   │   └── GoogleService-Info.plist.example  # Firebase config template
│   │
│   ├── Core/                # Core services and utilities
│   │   ├── Services/       # Business logic services
│   │   ├── Models/          # Data models
│   │   ├── UIComponents/    # Reusable UI components
│   │   └── Utilities/      # Helper utilities
│   │
│   ├── Features/            # Feature modules
│   │   ├── ContentGeneration/
│   │   ├── Reading/
│   │   ├── Authentication/
│   │   ├── History/
│   │   ├── Profile/
│   │   ├── Settings/
│   │   ├── OCR/
│   │   └── ...
│   │
│   └── Resources/           # Assets, fonts, localizations
│       ├── Assets.xcassets/
│       ├── Fonts/
│       └── Localizables/
│
├── Liroo.xcodeproj/         # Xcode project file
├── LirooWidgetExtension/    # iOS Widget extension
│
├── Backend-Orasync/         # Backend API service (Python/Flask)
│   ├── backend.py           # Main Flask application
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment variables template
│   ├── README.md            # Backend documentation
│   └── .gitignore
│
├── README.md                # This file
├── SETUP.md                 # Detailed setup guide
└── .gitignore              # Git ignore rules
```

> **All in one place!** No submodules, no complex setup. Just clone and go.

### Configuration System

The app uses a centralized configuration system (`AppConfig`) that:
- Supports environment variables for backend URL configuration
- Provides sensible defaults for development
- Allows easy switching between development and production environments
- Ensures no hardcoded credentials in the codebase

## Getting Started

### Prerequisites

- **Xcode 15.0+**: Latest Xcode with Swift 5.9 support
- **iOS 15.0+**: Device or simulator running iOS 15.0 or later
- **Python 3.9+**: For backend development (optional if using hosted backend)
- **Google Cloud Platform Account**: For Gemini API and Cloud Storage
- **Firebase Project**: For authentication and data storage

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/jaskirat1616/Liroo-Project.git
   cd Liroo-Project
   ```
   > **Note**: This is a single repository containing both iOS app and backend. No submodules required!

2. **Set up Firebase** (see [SETUP.md](SETUP.md) for detailed instructions)
   - Create Firebase project at [Firebase Console](https://console.firebase.google.com)
   - Download `GoogleService-Info.plist`
   - Copy `Liroo/Application/GoogleService-Info.plist.example` to `Liroo/Application/GoogleService-Info.plist`
   - Fill in your Firebase credentials from the downloaded file

3. **Configure Backend URL** (optional for local development)
   - For local development: Set `BACKEND_URL=http://localhost:5000` in Xcode scheme
   - For production: Set your deployed backend URL
   - Default: `http://localhost:5000` (can be changed in `Liroo/Core/Utilities/AppConfig.swift`)

4. **Open in Xcode and build**
   ```bash
   open Liroo.xcodeproj
   # Select your target device
   # Build and run (⌘R)
   ```

For detailed setup instructions, see [SETUP.md](SETUP.md).

### Backend Setup

The backend is required for content generation. See [Backend README](Backend-Orasync/README.md) for complete setup instructions.

**Quick Backend Setup:**
```bash
cd Backend-Orasync
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
flask --app backend:app run
```

## Configuration

### iOS App Configuration

**Backend URL**
- Set `BACKEND_URL` environment variable, or
- Update `AppConfig.backendURL` in `Liroo/Core/Utilities/AppConfig.swift`
- Default: `http://localhost:5000` (development)

**Firebase Configuration**
- Place `GoogleService-Info.plist` in `Liroo/Application/`
- Ensure bundle ID matches Firebase project
- Enable required Firebase services (Auth, Firestore, Storage)

### Backend Configuration

Create `.env` file in `Backend-Orasync/` directory:

```env
GENAI_API_KEY=your_gemini_api_key
GCS_BUCKET_NAME=your-gcs-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
BASE_URL=https://your-backend-url.run.app
```

See `.env.example` for all available options.

### Firebase Setup

1. Create Firebase project at [Firebase Console](https://console.firebase.google.com)
2. Enable services:
   - Authentication (Email/Password)
   - Firestore Database
   - Cloud Storage
3. Download `GoogleService-Info.plist` and add to project
4. Configure security rules for Firestore and Storage

### Google Cloud Setup

1. Create GCP project
2. Enable APIs:
   - Gemini API
   - Cloud Storage API
   - Text-to-Speech API
3. Create service account with Storage Admin role
4. Download service account JSON key
5. Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable

## Usage

### Generating Content

1. **Enter Text**: Type or paste text in the input field, or use OCR to extract from images
2. **Select Reading Level**: Choose Beginner, Moderate, or Intermediate
3. **Choose Content Type**: Select Story, Lecture, Comic, or Detailed Explanation
4. **Configure Options**:
   - For stories: Genre, main character, image style
   - For lectures: Image style
   - For comics: Comic style
5. **Generate**: Tap "Generate Content" and wait for processing
6. **View**: Tap generated content to view in full reading mode

### Using Text-to-Speech

1. Open any story or generated content
2. Tap the "Sound" button in the header
3. Listen to narration with friendly narrator voice
4. Control playback: Tap again to stop, or let it play through

### Customizing Reading Experience

1. Access Settings from Profile tab
2. Select reading theme (Light, Dark, Sepia, etc.)
3. Adjust font size (slider control)
4. Choose font style (System, OpenDyslexic, etc.)
5. Enable/disable dyslexia-friendly features

### OCR and File Import

1. **Camera OCR**: Tap "Camera" button, take photo, text is automatically extracted
2. **Photo Library**: Tap "Photos" button, select image, text is extracted
3. **File Import**: Tap "File Import", select PDF or image file
4. Extracted text appears in the input field automatically

## API Documentation

### Backend Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/process` | POST | General content generation |
| `/generate_story` | POST | Story generation |
| `/generate_lecture` | POST | Lecture generation with audio |
| `/generate_comic` | POST | Comic generation |
| `/generate_tts` | POST | Text-to-speech generation |
| `/generate_image` | POST | Image generation |
| `/progress/{request_id}` | GET | Check generation progress |
| `/health` | GET | Backend health status |

See [Backend README](Backend-Orasync/README.md) for detailed API documentation, request/response formats, and examples.

## Development

### Code Style

- Follow [Swift API Design Guidelines](https://swift.org/documentation/api-design-guidelines/)
- Use SwiftUI best practices and patterns
- Maintain consistent naming conventions
- Document public APIs with comments
- Use `MARK:` comments to organize code sections

### Project Organization

- Features are organized in separate modules
- Core services are reusable across features
- Models are separated by domain (App, Firebase, etc.)
- UI components are in `UIComponents` for reusability

### Testing

- **Unit Tests**: Test business logic and view models
- **UI Tests**: Test critical user flows
- **Integration Tests**: Test API interactions and data flow

### Building

```bash
# Open project
open Liroo.xcodeproj

# Build for simulator
xcodebuild -scheme Liroo -sdk iphonesimulator

# Build for device (requires signing)
xcodebuild -scheme Liroo -sdk iphoneos
```

## Contributing

We welcome contributions! Please follow these guidelines:

### Getting Started

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Ensure code follows style guidelines
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Contribution Guidelines

- Follow existing code style and patterns
- Write clear commit messages
- Add documentation for new features
- Update README if adding new features
- Ensure all tests pass
- Test on both iPhone and iPad if UI changes

### Reporting Issues

- Use GitHub Issues for bug reports
- Include steps to reproduce
- Provide device/iOS version information
- Include relevant logs or screenshots

## Security

### Best Practices

- **Never commit sensitive files**: `.env`, `GoogleService-Info.plist`, service account keys
- **Use environment variables**: All configuration should use environment variables
- **Rotate API keys**: Regularly rotate API keys and credentials
- **Review Firebase rules**: Ensure Firestore and Storage security rules are properly configured
- **Implement authentication**: Use Firebase Authentication for user management
- **HTTPS only**: Use HTTPS for all API communications
- **Rate limiting**: Implement rate limiting in production backend

### Security Checklist

Before deploying:
- [ ] All sensitive files are in `.gitignore`
- [ ] No hardcoded credentials in code
- [ ] Environment variables are properly configured
- [ ] Firebase security rules are reviewed
- [ ] API keys have proper restrictions
- [ ] CORS is properly configured
- [ ] HTTPS is enabled for all endpoints

## License

[Specify your license here - e.g., MIT, Apache 2.0, etc.]

## Acknowledgments

- **Google Gemini**: AI capabilities for content generation
- **Firebase**: Backend services and infrastructure
- **Apple**: SwiftUI framework and development tools
- **Open Source Community**: Various open source libraries and tools

## Additional Resources

- [Setup Guide](SETUP.md) - Detailed setup instructions
- [Backend Documentation](Backend-Orasync/README.md) - Backend API documentation
- [Firebase Documentation](https://firebase.google.com/docs) - Firebase setup and usage
- [Google Cloud Documentation](https://cloud.google.com/docs) - GCP services documentation

---

<div align="center">
  Made with ❤️ using SwiftUI
</div>
