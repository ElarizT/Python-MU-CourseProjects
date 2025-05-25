#!/bin/bash
# deploy_template_fix.sh - Deploy the template fix

echo "Preparing template fix deployment..."

# 1. Verify template fix
echo "Verifying template fix locally..."
python fix_template.py

if [ $? -ne 0 ]; then
    echo "Template verification failed! Fix the template before deploying."
    exit 1
fi

# 2. Run template render test
echo "Running full template render test..."
python test_template_render.py

if [ $? -ne 0 ]; then
    echo "Template render test failed! Fix the template before deploying."
    exit 1
fi

# 3. Prepare git commit
echo "Would you like to commit the template fixes? (y/n)"
read commit

if [ "$commit" = "y" ]; then
    git add templates/index.html
    git add templates/index_fixed.html
    git add static/css/landing-page.css
    git add static/js/landing-page.js
    git add fix_template.py
    git add Procfile
    git add render.yaml
    git add TEMPLATE_FIX.md
    git add DEPLOYMENT_STEPS.md
    
    git commit -m "Fix Jinja2 template syntax error in index.html"
    
    echo "Would you like to push the changes? (y/n)"
    read push
    
    if [ "$push" = "y" ]; then
        git push
        echo "Changes pushed to repository"
    fi
fi

# 4. Deploy instructions
echo ""
echo "Deployment Instructions:"
echo "1. Deploy to Render using the Render dashboard or CLI"
echo "2. Monitor the deployment logs for any template errors"
echo "3. Verify the landing page loads properly once deployed"
echo "4. Run the template monitor to check for correct rendering:"
echo "   python monitor_template.py --url your-app-url.onrender.com --retry 3 --wait 10"

echo ""
echo "Template fix deployment preparation completed!"