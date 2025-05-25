#!/bin/bash
# deploy_functions.sh - Script to deploy Firebase Cloud Functions

echo "Deploying Firebase Cloud Functions..."

# Navigate to the functions directory
cd functions

# Install dependencies
echo "Installing dependencies..."
npm install

# Build the TypeScript code
echo "Building functions..."
npm run build

# Deploy functions with environment configuration
echo "Deploying functions to Firebase..."
firebase deploy --only functions --project $FIREBASE_PROJECT_ID

# Deploy scheduler token
echo "Setting up scheduler token for secure Cloud Scheduler access..."
firebase functions:config:set scheduler.token="$(openssl rand -base64 24)" --project $FIREBASE_PROJECT_ID

echo "Deployment complete!"
echo "To set up Cloud Scheduler, run the following gcloud command:"
echo "gcloud scheduler jobs create http reset-daily-tokens --schedule=\"0 0 * * *\" \\"
echo "  --uri=\"https://us-central1-$FIREBASE_PROJECT_ID.cloudfunctions.net/resetDailyTokenUsage\" \\"
echo "  --http-method=POST \\"
echo "  --headers=\"Authorization=Bearer \$(firebase functions:config:get scheduler.token --project $FIREBASE_PROJECT_ID | grep token | cut -d' ' -f2 | tr -d '\"')\" \\"
echo "  --time-zone=\"UTC\""