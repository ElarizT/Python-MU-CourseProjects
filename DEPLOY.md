# LightYearAI Deployment Guide

This guide provides instructions for deploying LightYearAI to Render.com.

## Prerequisites

1. A Render.com account
2. A Firebase project with Firebase Authentication enabled
3. Firebase Admin SDK service account credentials

## Setup Steps

### 1. Prepare Environment Variables

The following environment variables need to be set in Render:

```
# API Keys
GOOGLE_API_KEY=your_google_api_key
GEMINI_API_KEY=your_gemini_api_key

# Firebase Configuration
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_DATABASE_URL=https://your_project.firebasedatabase.app
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_project.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id
FIREBASE_MEASUREMENT_ID=your_measurement_id

# Secret Key for Flask Sessions
FLASK_SECRET_KEY=generate_a_secure_random_key

# Firebase Service Account Credentials (Base64 encoded)
FIREBASE_CREDENTIALS_BASE64=your_base64_encoded_credentials
```

### 2. Encode Firebase Credentials

To encode your Firebase service account credentials (JSON file):

```bash
python deploy_firebase_credentials.py --file path/to/your-credentials-file.json --verify
```

Copy the output and set it as the `FIREBASE_CREDENTIALS_BASE64` environment variable in Render.

### 3. Deploy to Render

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Use the settings from render.yaml
4. Set all the environment variables
5. Deploy

## Troubleshooting

If you encounter authentication issues:

1. Check the `/api/server-health` endpoint to verify environment variables
2. Ensure Firebase configuration matches exactly with your Firebase Console settings
3. Verify the service account has the necessary permissions
4. Check that FIREBASE_STORAGE_BUCKET is set to the correct value (your_project.firebasestorage.app)

## Firebase Authentication

The application supports:

1. Email/password authentication
2. Google authentication (popup and redirect methods)

Make sure these methods are enabled in your Firebase Console.
