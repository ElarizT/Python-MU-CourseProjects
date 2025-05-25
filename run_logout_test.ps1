# Firebase Logout Test Runner
# This script helps test the Firebase logout functionality

Write-Host "=============================================" -ForegroundColor Green
Write-Host "Firebase Logout Test Runner" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""

# Check if Python is installed for running a simple server
$pythonInstalled = $null
try {
    $pythonInstalled = python --version
} catch {
    try {
        $pythonInstalled = py --version
    } catch {
        Write-Host "Python not found. Please install Python to run this test." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Python found: $pythonInstalled" -ForegroundColor Green
Write-Host "Starting test server..."

# Change to the directory where our test files are
Set-Location -Path "c:\Users\taghi\.anaconda"

# Create a simple HTTP server to serve our test page
$pythonCommand = if ($pythonInstalled -match "Python 3") { "python" } else { "py" }
Write-Host "Starting HTTP server using $pythonCommand..." -ForegroundColor Yellow

# Start a Python simple HTTP server
Write-Host "Running server at http://localhost:8000"
Write-Host "Please open this URL in your browser to run the test:"
Write-Host "http://localhost:8000/firebase_logout_test.html" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server when done." -ForegroundColor Yellow

# Start the server
& $pythonCommand -m http.server 8000

# This point will only be reached after the server is stopped with Ctrl+C
Write-Host ""
Write-Host "Test server stopped." -ForegroundColor Green
