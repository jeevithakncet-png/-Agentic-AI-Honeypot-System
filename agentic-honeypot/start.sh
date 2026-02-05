#!/bin/bash
# Startup script for Agentic Honeypot API

echo "=================================="
echo "Agentic Honeypot API - Startup"
echo "=================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✓ Created .env file. Please update with your settings."
fi

# Check Python installation
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD=$(command -v python3 || command -v python)
echo "Using Python: $PYTHON_CMD"

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt

# Start API
echo ""
echo "🚀 Starting Agentic Honeypot API..."
echo ""
echo "📍 API URL: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "To test the API:"
echo "  python test_api.py"
echo ""

# Run uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
