# deploy_template_fix.ps1
# PowerShell script to deploy the template fix

Write-Host "Preparing template fix deployment..." -ForegroundColor Cyan

# 1. Verify template fix
Write-Host "Verifying template fix locally..." -ForegroundColor Yellow
python fix_template.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Template verification failed! Fix the template before deploying." -ForegroundColor Red
    exit 1
}

# 2. Run template render test
Write-Host "Running full template render test..." -ForegroundColor Yellow
python test_template_render.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Template render test failed! Fix the template before deploying." -ForegroundColor Red
    exit 1
}

# 3. Prepare git commit
Write-Host "Would you like to commit the template fixes? (y/n)" -ForegroundColor Green
$commit = Read-Host

if ($commit -eq "y") {
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
    
    Write-Host "Would you like to push the changes? (y/n)" -ForegroundColor Green
    $push = Read-Host
    
    if ($push -eq "y") {
        git push
        Write-Host "Changes pushed to repository" -ForegroundColor Green
    }
}

# 4. Deploy instructions
Write-Host "`nDeployment Instructions:" -ForegroundColor Cyan
Write-Host "1. Deploy to Render using the Render dashboard or CLI"
Write-Host "2. Monitor the deployment logs for any template errors"
Write-Host "3. Verify the landing page loads properly once deployed"
Write-Host "4. Run the template monitor to check for correct rendering:"
Write-Host "   python monitor_template.py --url your-app-url.onrender.com --retry 3 --wait 10" -ForegroundColor Yellow

Write-Host "`nTemplate fix deployment preparation completed!" -ForegroundColor Green