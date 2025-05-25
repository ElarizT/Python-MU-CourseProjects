#!/bin/bash
# LightYearAI Environment Variables Setup Script

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    exit 1
fi

# Source the .env file
set -a
source .env
set +a

# Generate base64 encoded Firebase credentials
if [ -z "$1" ]; then
    # Try to find the credentials file
    CRED_FILE="$GOOGLE_APPLICATION_CREDENTIALS"
    
    if [ ! -f "$CRED_FILE" ]; then
        echo "Error: Firebase credentials file not found at $CRED_FILE"
        echo "Usage: $0 [path/to/credentials.json]"
        exit 1
    fi
else
    CRED_FILE="$1"
fi

echo "Encoding Firebase credentials file: $CRED_FILE"
python deploy_firebase_credentials.py --file "$CRED_FILE" --verify

# Print deployment instructions
echo ""
echo "============= DEPLOYMENT INSTRUCTIONS ============="
echo "1. Create a new web service on Render.com"
echo "2. Connect your repository"
echo "3. Set the following environment variables:"
echo ""
echo "GOOGLE_API_KEY=$GOOGLE_API_KEY"
echo "GEMINI_API_KEY=$GEMINI_API_KEY"
echo "FIREBASE_API_KEY=$FIREBASE_API_KEY"
echo "FIREBASE_AUTH_DOMAIN=$FIREBASE_AUTH_DOMAIN"
echo "FIREBASE_DATABASE_URL=$FIREBASE_DATABASE_URL"
echo "FIREBASE_PROJECT_ID=$FIREBASE_PROJECT_ID"
echo "FIREBASE_STORAGE_BUCKET=$FIREBASE_STORAGE_BUCKET"
echo "FIREBASE_MESSAGING_SENDER_ID=$FIREBASE_MESSAGING_SENDER_ID"
echo "FIREBASE_APP_ID=$FIREBASE_APP_ID"
echo "FIREBASE_MEASUREMENT_ID=$FIREBASE_MEASUREMENT_ID"
echo "FLASK_SECRET_KEY=$FLASK_SECRET_KEY"
echo "FIREBASE_CREDENTIALS_BASE64=[value from above]"
echo ""
echo "4. Deploy your application"
echo "=================================================="
