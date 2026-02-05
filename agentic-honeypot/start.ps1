# Startup script for Agentic Honeypot API (Windows)

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Agentic Honeypot API - Startup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Created .env file. Please update with your settings." -ForegroundColor Green
}

# Check Python installation
$python_cmd = $null
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $python_cmd = "python3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $python_cmd = "python"
} else {
    Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

Write-Host "Using Python: $python_cmd" -ForegroundColor Green

# Check virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    & $python_cmd -m venv .venv
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "📚 Installing dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt

# Start API
Write-Host ""
Write-Host "🚀 Starting Agentic Honeypot API..." -ForegroundColor Green
Write-Host ""
Write-Host "📍 API URL: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📖 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "To test the API:" -ForegroundColor Cyan
Write-Host "  python test_api.py" -ForegroundColor Gray
Write-Host ""

# Run uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
