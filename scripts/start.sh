#!/bin/bash

# Music Tools API - Start Script

set -e

echo "🎵 Starting Music Tools API Service..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/uploads data/outputs data/logs

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✏️  Please edit .env file to configure the API service."
fi

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if API is responding
echo "🔍 Checking API health..."
API_PORT=$(docker-compose port music-tools-api 8000 2>/dev/null | cut -d: -f2 || echo "8001")
for i in {1..30}; do
    if curl -f http://localhost:${API_PORT}/health &> /dev/null; then
        echo "✅ API is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ API failed to start properly"
        echo "📋 Checking logs..."
        docker-compose logs music-tools-api
        exit 1
    fi
    sleep 2
done

echo ""
echo "🎉 Music Tools API Service is running!"
echo ""
echo "📋 Service Information:"
echo "   API URL:        http://localhost:${API_PORT}"
echo "   Documentation:  http://localhost:${API_PORT}/docs"
echo "   Health Check:   http://localhost:${API_PORT}/health"
echo ""
echo "🔧 Useful Commands:"
echo "   Stop:           docker-compose down"
echo "   Restart:        docker-compose restart"
echo "   Logs:           docker-compose logs -f"
echo "   Status:         docker-compose ps"
echo ""
echo "📁 Data Directories:"
echo "   Uploads:        ./data/uploads"
echo "   Outputs:        ./data/outputs"
echo "   Logs:           ./data/logs"
echo ""
echo "💡 Tips:"
echo "   - First run may take longer (downloading AI models)"
echo "   - Check logs if you encounter issues"
echo "   - Edit .env file to customize configuration"
