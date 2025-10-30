#!/bin/bash

# Set script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Setting up and starting Hackathon backend..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Create a function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down server..."
    kill $BACKEND_PID 2>/dev/null
    exit
}

# Trap Ctrl+C and call cleanup
trap cleanup INT TERM

# Start backend server
echo "🐍 Starting backend server on http://127.0.0.1:5000..."
cd HackathonBE
"$SCRIPT_DIR/venv/bin/python" app.py &
BACKEND_PID=$!
cd ..

echo ""
echo "✅ Setup complete!"
echo "🔧 Backend: http://127.0.0.1:5000"
echo ""
echo "Press Ctrl+C to stop the server..."

# Wait for backend process
wait $BACKEND_PID
