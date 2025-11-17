#!/bin/bash
# Start Web UI Server

# Load environment variables from .zshrc
source ~/.zshrc 2>/dev/null || true

# Change to project directory
cd "$(dirname "$0")"

echo "🌐 Starting Web UI Server..."
echo "📍 Server will run on http://localhost:8000"
echo ""

# Check if credentials file exists
if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "⚠️  Warning: GOOGLE_APPLICATION_CREDENTIALS file not found!"
    echo "   Path: $GOOGLE_APPLICATION_CREDENTIALS"
    echo ""
fi

# Use Anaconda Python (or system Python if anaconda not available)
PYTHON_CMD="python"
if [ -f "/opt/anaconda3/bin/python" ]; then
    PYTHON_CMD="/opt/anaconda3/bin/python"
    echo "🐍 Using Anaconda Python: $PYTHON_CMD"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "🐍 Using Python3: $PYTHON_CMD"
fi

# Check if uvicorn is installed
if ! $PYTHON_CMD -m uvicorn --help &> /dev/null; then
    echo "⚠️  uvicorn not found. Installing dependencies..."
    $PYTHON_CMD -m pip install -r requirements.txt
    echo ""
fi

# Start the API server (no web UI - pure backend)
$PYTHON_CMD -m uvicorn app.api:app --reload --port 8000 --host 0.0.0.0

