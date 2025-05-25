# Initialize_Git_Repo.ps1 - Script to properly set up git repo for LightYearAI

Write-Host "Setting up git repository for LightYearAI..." -ForegroundColor Green

# Initialize git repo if not already done
if (-not (Test-Path ".git")) {
    git init
    Write-Host "Git repository initialized" -ForegroundColor Green
} else {
    Write-Host "Git repository already exists" -ForegroundColor Yellow
}

# Make sure .gitignore is properly set up
if (Test-Path ".gitignore") {
    Write-Host ".gitignore already exists" -ForegroundColor Yellow
} else {
    Write-Host "Creating .gitignore file" -ForegroundColor Green
    @"
# Dependencies
node_modules
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Sensitive information
*.env
*.env.sample
*-firebase-adminsdk-*.json
lightyearai-app-firebase-adminsdk-*.json

# User uploads
uploads/

# Logs
*.log
logs/

# Local development
.vscode/
.idea/
*.swp
*.swo

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
"@ | Out-File -FilePath ".gitignore" -Encoding utf8
}

# Add all important files
Write-Host "Adding application files to git..." -ForegroundColor Green
git add app.py app_fixed.py
git add excel_generator.py file_utils.py
git add firebase_auth_utils.py firebase_chat_utils.py firebase_diagnostics.py firebase_utils.py
git add firebase.json firestore.indexes.json firestore.rules
git add fix_template.py fix_template_syntax.sh monitor_template.py
git add presentation_builder.py
git add Procfile pytest.ini
git add quick_template_fix.sh
git add referral_stats_endpoint.py referral_utils.py
git add render.yaml requirements.txt
git add subscription_utils.py
git add test_*.py
git add *.md

# Add directories
Write-Host "Adding application directories to git..." -ForegroundColor Green
git add templates/ static/ agents/ functions/ mcp/ scripts/ tests/

Write-Host "Git repository setup complete!" -ForegroundColor Green
Write-Host "Now you can commit your changes:" -ForegroundColor Cyan
Write-Host "  git commit -m 'Initial commit'" -ForegroundColor Cyan
Write-Host "Then add your GitHub repo as remote and push:" -ForegroundColor Cyan
Write-Host "  git remote add origin <your-github-repo-url>" -ForegroundColor Cyan
Write-Host "  git push -u origin main" -ForegroundColor Cyan
