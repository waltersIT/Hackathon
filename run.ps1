# Set execution policy for this process
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "🚀 Setting up and starting Hackathon backend..." -ForegroundColor Cyan

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed. Please install Python first." -ForegroundColor Red
    exit 1
}

# Create virtual environment if it doesn't exist
if (-Not (Test-Path "venv")) {
    Write-Host "📦 Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install Python dependencies
Write-Host "📥 Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Function to handle cleanup
function Cleanup {
    Write-Host ""
    Write-Host "🛑 Shutting down server..." -ForegroundColor Yellow
    if ($backendJob) {
        Stop-Job $backendJob
        Remove-Job $backendJob
    }
    exit
}

# Register cleanup function for Ctrl+C
[Console]::TreatControlCAsInput = $false
$null = Register-EngineEvent PowerShell.Exiting -Action { Cleanup }

# Start backend server
Write-Host "🐍 Starting backend server on http://127.0.0.1:5000..." -ForegroundColor Green
Set-Location HackathonBE
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:ScriptDir\HackathonBE
    & "..\venv\Scripts\python.exe" app.py
}
Set-Location ..

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host "🔧 Backend: http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server..." -ForegroundColor Yellow

# Wait for user to press Ctrl+C
try {
    while ($true) {
        Start-Sleep -Seconds 1
        # Check if backend job is still running
        if ($backendJob.State -eq "Completed" -or $backendJob.State -eq "Failed") {
            Receive-Job $backendJob
            break
        }
    }
} catch {
    Cleanup
}

Cleanup
