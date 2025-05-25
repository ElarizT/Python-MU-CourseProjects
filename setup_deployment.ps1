# LightYearAI Environment Variables Setup Script for Windows

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Error "Error: .env file not found!"
    exit 1
}

# Parse the .env file and set environment variables
Get-Content ".env" | ForEach-Object {
    if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

# Get credentials file path
$credFile = $env:GOOGLE_APPLICATION_CREDENTIALS
if ($args.Count -gt 0) {
    $credFile = $args[0]
}

if (-not (Test-Path $credFile)) {
    Write-Error "Error: Firebase credentials file not found at $credFile"
    Write-Host "Usage: .\setup_deployment.ps1 [path/to/credentials.json]"
    exit 1
}

Write-Host "Encoding Firebase credentials file: $credFile"
python deploy_firebase_credentials.py --file "$credFile" --verify

# Print deployment instructions
Write-Host ""
Write-Host "============= DEPLOYMENT INSTRUCTIONS ============="
Write-Host "1. Create a new web service on Render.com"
Write-Host "2. Connect your repository"
Write-Host "3. Set the following environment variables:"
Write-Host ""
Write-Host "GOOGLE_API_KEY=$env:GOOGLE_API_KEY"
Write-Host "GEMINI_API_KEY=$env:GEMINI_API_KEY"
Write-Host "FIREBASE_API_KEY=$env:FIREBASE_API_KEY"
Write-Host "FIREBASE_AUTH_DOMAIN=$env:FIREBASE_AUTH_DOMAIN"
Write-Host "FIREBASE_DATABASE_URL=$env:FIREBASE_DATABASE_URL" 
Write-Host "FIREBASE_PROJECT_ID=$env:FIREBASE_PROJECT_ID"
Write-Host "FIREBASE_STORAGE_BUCKET=$env:FIREBASE_STORAGE_BUCKET"
Write-Host "FIREBASE_MESSAGING_SENDER_ID=$env:FIREBASE_MESSAGING_SENDER_ID"
Write-Host "FIREBASE_APP_ID=$env:FIREBASE_APP_ID"
Write-Host "FIREBASE_MEASUREMENT_ID=$env:FIREBASE_MEASUREMENT_ID"
Write-Host "FLASK_SECRET_KEY=$env:FLASK_SECRET_KEY"
Write-Host "FIREBASE_CREDENTIALS_BASE64=[value from above]"
Write-Host ""
Write-Host "4. Deploy your application"
Write-Host "=================================================="
