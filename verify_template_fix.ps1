# verify_template_fix.ps1
# PowerShell script to verify the template fix locally

Write-Host "Testing index.html template syntax..." -ForegroundColor Cyan

# Paths
$indexTemplatePath = ".\templates\index.html"
$fixedTemplatePath = ".\templates\index_fixed.html"

if (Test-Path $indexTemplatePath) {
    Write-Host "Found template at $indexTemplatePath" -ForegroundColor Green
      # Test the template with Python
    Write-Host "Testing original template syntax..." -ForegroundColor Yellow
    $originalResult = python -c "
try:
    import jinja2
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
    template = env.get_template('index.html')
    print('SUCCESS: Template syntax is valid!')
except Exception as e:
    print('ERROR:', str(e))
"
    
    Write-Host $originalResult -ForegroundColor $(if ($originalResult -match "ERROR") { "Red" } else { "Green" })
    
    if ($originalResult -match "ERROR") {
        Write-Host "Original template has syntax errors. Testing fixed version..." -ForegroundColor Yellow
        
        if (Test-Path $fixedTemplatePath) {            $fixedResult = python -c "
try:
    import jinja2
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
    template = env.get_template('index_fixed.html')
    print('SUCCESS: Fixed template syntax is valid!')
except Exception as e:
    print('ERROR:', str(e))
"
            Write-Host $fixedResult -ForegroundColor $(if ($fixedResult -match "ERROR") { "Red" } else { "Green" })
            
            if ($fixedResult -match "SUCCESS") {
                Write-Host "Would you like to replace the original template with the fixed version? (y/n)" -ForegroundColor Yellow
                $response = Read-Host
                
                if ($response -eq "y") {
                    # Backup original
                    Copy-Item $indexTemplatePath -Destination "$indexTemplatePath.backup"
                    Write-Host "Created backup at $indexTemplatePath.backup" -ForegroundColor Gray
                    
                    # Replace with fixed version
                    Copy-Item $fixedTemplatePath -Destination $indexTemplatePath -Force
                    Write-Host "Replaced original template with fixed version." -ForegroundColor Green
                    
                    # Verify again                    $finalResult = python -c "
try:
    import jinja2
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
    template = env.get_template('index.html')
    print('SUCCESS: Template syntax is now valid!')
except Exception as e:
    print('ERROR:', str(e))
"
                    Write-Host $finalResult -ForegroundColor $(if ($finalResult -match "ERROR") { "Red" } else { "Green" })
                }
                else {
                    Write-Host "No changes applied." -ForegroundColor Yellow
                }
            }
        }
        else {
            Write-Host "Fixed template not found at $fixedTemplatePath" -ForegroundColor Red
        }
    }
}
else {
    Write-Host "Template not found at $indexTemplatePath" -ForegroundColor Red
}

Write-Host "Template verification completed." -ForegroundColor Cyan
