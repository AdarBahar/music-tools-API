#!/bin/bash

# Music Tools API - Quick Start Script
# This script helps you get the Music Tools API running quickly

set -e

echo "🎵 Music Tools API - Quick Start"
echo "================================"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install with package manager
install_with_manager() {
    if command_exists apt-get; then
        echo "📦 Installing with apt-get..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv ffmpeg redis-server
        sudo systemctl start redis-server
        sudo systemctl enable redis-server
    elif command_exists yum; then
        echo "📦 Installing with yum..."
        sudo yum install -y python3 python3-pip ffmpeg redis
        sudo systemctl start redis
        sudo systemctl enable redis
    elif command_exists dnf; then
        echo "📦 Installing with dnf..."
        sudo dnf install -y python3 python3-pip ffmpeg redis
        sudo systemctl start redis
        sudo systemctl enable redis
    elif command_exists brew; then
        echo "📦 Installing with Homebrew..."
        brew install python@3.10 ffmpeg redis
        brew services start redis
    else
        echo "❌ No supported package manager found."
        echo "Please install Python 3.8+, FFmpeg, and Redis manually."
        exit 1
    fi
}

# Check what's available
echo "🔍 Checking system requirements..."

# Check for Docker first (recommended path)
if command_exists docker && command_exists docker-compose; then
    echo "✅ Docker and Docker Compose found"
    echo ""
    echo "🚀 Starting with Docker (recommended)..."
    
    # Create data directories
    mkdir -p data/uploads data/outputs data/logs
    
    # Copy environment file
    if [ ! -f .env ]; then
        cp .env.example .env
        echo "📝 Created .env file from template"
    fi
    
    # Start services
    echo "🔨 Building and starting services..."
    docker-compose up -d --build
    
    # Wait and check
    echo "⏳ Waiting for services to start..."
    sleep 15
    
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo ""
        echo "🎉 Success! Music Tools API is running!"
        echo ""
        echo "📋 Access your API:"
        echo "   API URL:        http://localhost:8000"
        echo "   Documentation:  http://localhost:8000/docs"
        echo "   Health Check:   http://localhost:8000/health"
        echo ""
        echo "🔧 Management commands:"
        echo "   Stop:    docker-compose down"
        echo "   Restart: docker-compose restart"
        echo "   Logs:    docker-compose logs -f"
    else
        echo "❌ Service failed to start. Check logs with: docker-compose logs"
        exit 1
    fi

elif command_exists python3; then
    echo "✅ Python 3 found"
    
    # Check for other dependencies
    missing_deps=()
    
    if ! command_exists ffmpeg; then
        missing_deps+=("ffmpeg")
    fi
    
    if ! command_exists redis-server && ! command_exists redis-cli; then
        missing_deps+=("redis")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo "❌ Missing dependencies: ${missing_deps[*]}"
        echo ""
        read -p "Would you like to install missing dependencies? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_with_manager
        else
            echo "Please install the missing dependencies manually and run this script again."
            exit 1
        fi
    fi
    
    echo ""
    echo "🚀 Starting with manual installation..."
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    echo "📥 Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Copy environment file
    if [ ! -f .env ]; then
        cp .env.example .env
        echo "📝 Created .env file from template"
    fi
    
    # Start Redis if not running
    if ! pgrep redis-server > /dev/null; then
        echo "🔴 Starting Redis..."
        if command_exists systemctl; then
            sudo systemctl start redis-server
        elif command_exists brew; then
            brew services start redis
        else
            redis-server --daemonize yes
        fi
    fi
    
    # Start the API
    echo "🚀 Starting Music Tools API..."
    echo "Press Ctrl+C to stop the service"
    echo ""
    python main.py

else
    echo "❌ Python 3 not found"
    echo ""
    echo "Please install Python 3.8 or higher and try again."
    echo ""
    echo "Installation options:"
    echo "  - Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "  - CentOS/RHEL:   sudo yum install python3 python3-pip"
    echo "  - macOS:         brew install python@3.10"
    echo "  - Windows:       Download from https://python.org"
    exit 1
fi
