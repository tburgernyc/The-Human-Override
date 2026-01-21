#!/bin/bash
set -e

echo "🔧 Setting up The Human Override environment..."

# 1. System Dependencies (Linux)
if [ -f /etc/debian_version ]; then
    echo "📦 Installing system libraries (Debian/Ubuntu)..."
    sudo apt-get update
    sudo apt-get install -y python3-venv python3-pip ffmpeg
elif [ -f /etc/redhat-release ]; then
    echo "📦 Installing system libraries (RHEL/CentOS)..."
    sudo yum install -y python3-pip ffmpeg
elif [[ "$OSTYPE" == "darwin"* ]]; then
     echo "📦 MacOS detected. ensuring ffmpeg is installed via brew..."
     if ! command -v ffmpeg &> /dev/null; then
        brew install ffmpeg
     fi
else
    echo "⚠️  OS not strictly recognized. Please ensure 'ffmpeg' is installed."
fi

# 2. Python Environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "🔌 Activating virtual environment..."
source venv/bin/activate

echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Setup Complete!"
echo "To start, run: source venv/bin/activate"
echo "Then use: python main.py --help"
