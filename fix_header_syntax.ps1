# Fix Header Syntax Error Script for Windows PowerShell
# This script fixes the syntax error in app.py at line 4740

# Create a backup of the original file
Copy-Item -Path "app.py" -Destination "app.py.header.bak" -Force
Write-Host "Created backup at app.py.header.bak"

# Read the content of app.py
$content = Get-Content -Path "app.py" -Raw

# Fix the syntax error by adding a line break
$pattern = "(response\.headers\['Expires'\] = '0')\s+(response\.headers\['X-Firebase-Reset'\])"
$replacement = "`$1`n    `$2"
$fixedContent = $content -replace $pattern, $replacement

# Check if a change was made
if ($fixedContent -eq $content) {
    Write-Host "Warning: No changes were made. The pattern might not match."
    exit 1
}

# Write the fixed content back to the file
Set-Content -Path "app.py" -Value $fixedContent
Write-Host "Successfully fixed syntax error in app.py at line 4740!"

# Ask if the user wants to commit and push the change
$deploy = Read-Host "Do you want to commit and push this fix? (y/n)"
if ($deploy -eq "y") {
    try {
        git add app.py
        git commit -m "Fix syntax error in app.py line 4740"
        git push
        Write-Host "Fix deployed!"
    } catch {
        Write-Host "Error during deployment: $_"
    }
} else {
    Write-Host "Fix applied but not deployed. Manually push when ready."
}
