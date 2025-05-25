# Fix Duplicate Logout Route and Syntax Errors

$ErrorActionPreference = "Stop"

Write-Host "Creating fixed version of app.py..." -ForegroundColor Cyan

# Create backup of original file
Copy-Item -Path app.py -Destination app.py.bak

# Read the content of the file
$content = Get-Content -Path app.py -Raw

# Use regex to remove the duplicate route definition and implementation
$pattern1 = '@app\.route\(''\/logout_cleanup''\)[^@]*?session\[''explicitly_logged_out''\] = True[^\r\n]*\r?\n'
$content = $content -replace $pattern1, ''

$pattern2 = '# Log the logout page request[^@]*?return render_template\(''logout\.html''[^\r\n]*\r?\n'
$content = $content -replace $pattern2, ''

# Add a note for clarity
$content = $content -replace 'return response, 200', "return response, 200`n`n# Note: /logout_cleanup route is defined elsewhere"

# Fix syntax error in the redirect line
$content = $content -replace 'resp = redirect\(url_for\(''index''\)\)\s+resp\.delete_cookie', "resp = redirect(url_for('index'))`n    resp.delete_cookie"

# Write the fixed content back to the file
$content | Set-Content -Path app.py

Write-Host "Fixed app.py created!" -ForegroundColor Green
Write-Host "To deploy, commit and push the changes to your repository." -ForegroundColor Yellow

# Optional: deployment to Render.com directly
Write-Host ""
$deployChoice = Read-Host "Would you like to deploy this fix to Render.com now? (y/n)"

if ($deployChoice -eq "y" -or $deployChoice -eq "Y") {
    Write-Host "Deploying fix to Render.com..." -ForegroundColor Cyan
    git add app.py
    git commit -m "Fix duplicate logout_cleanup route and syntax error"
    git push
    Write-Host "Deployment initiated. Check Render dashboard for deployment status." -ForegroundColor Green
}
else {
    Write-Host "No deployment made. You can manually review and deploy when ready." -ForegroundColor Yellow
}
