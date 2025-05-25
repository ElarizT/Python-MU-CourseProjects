#!/bin/bash
# Fix script for Firebase logout route conflict in app.py

# This script will create a fixed version of app.py that can be deployed
# to fix the duplicate logout_cleanup route issue and syntax errors

echo "Creating fixed version of app.py..."

# Create backup of original file
cp app.py app.py.bak

# Use sed to fix the duplicate route issue
# 1. Remove the duplicate route definition
sed -i '/^@app\.route.*logout_cleanup.*$/,/^    session\['\''explicitly_logged_out'\''\] = True$/d' app.py

# 2. Remove the remaining implementation of the duplicate route
sed -i '/^    # Log the logout page request$/,/^    return render_template.*logout\.html.*$/d' app.py

# 3. Add a comment for clarity
sed -i 's/return response, 200/return response, 200\n\n# Note: \/logout_cleanup route is defined elsewhere/' app.py

# 4. Fix syntax error in redirect line
sed -i 's/resp = redirect(url_for('\''index'\''))    resp.delete_cookie/resp = redirect(url_for('\''index'\''))\n    resp.delete_cookie/' app.py

echo "Fixed app.py created!"
echo "To deploy, run: git add app.py && git commit -m 'Fix duplicate logout_cleanup route and syntax errors' && git push"

# Optional: deployment to Render.com directly
echo ""
echo "Would you like to deploy this fix to Render.com now? (y/n)"
read -r deploy_choice

if [ "$deploy_choice" = "y" ] || [ "$deploy_choice" = "Y" ]; then
    echo "Deploying fix to Render.com..."
    git add app.py
    git commit -m "Fix duplicate logout_cleanup route and syntax error"
    git push
    echo "Deployment initiated. Check Render dashboard for deployment status."
else
    echo "No deployment made. You can manually review and deploy when ready."
fi
