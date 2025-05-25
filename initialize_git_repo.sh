#!/bin/bash
# initialize_git_repo.sh - Script to properly set up git repo for LightYearAI

echo "Setting up git repository for LightYearAI..."

# Initialize git repo if not already done
if [ ! -d ".git" ]; then
  git init
  echo "Git repository initialized"
else
  echo "Git repository already exists"
fi

# Make sure .gitignore is properly set up
if [ -f ".gitignore" ]; then
  echo ".gitignore already exists"
else
  echo "Creating .gitignore file"
  cat > .gitignore << 'EOL'
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
EOL
fi

# Add all important files
echo "Adding application files to git..."
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
echo "Adding application directories to git..."
git add templates/ static/ agents/ functions/ mcp/ scripts/ tests/

echo "Git repository setup complete!"
echo "Now you can commit your changes:"
echo "  git commit -m 'Initial commit'"
echo "Then add your GitHub repo as remote and push:"
echo "  git remote add origin <your-github-repo-url>"
echo "  git push -u origin main"
