#!/bin/bash

echo "🚀 Starting GrowthBook Exposure API Server..."

# Check if we're in the right directory
if [ ! -f "exposure_api.py" ]; then
    echo "❌ Error: exposure_api.py not found in current directory"
    echo "Please run this script from the adhoc directory"
    exit 1
fi

# Install dependencies if needed
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Start the FastAPI server
echo "🌐 Starting server on http://localhost:8000"
echo "📖 API documentation will be available at http://localhost:8000/docs"
echo "🔍 Health check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 exposure_api.py
