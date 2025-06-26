#!/bin/bash

# Music Tools API - Stop Script

set -e

echo "🛑 Stopping Music Tools API Service..."

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    exit 1
fi

# Stop services
echo "⏹️  Stopping services..."
docker-compose down

echo "✅ Music Tools API Service stopped successfully!"
echo ""
echo "💡 To start again, run: ./scripts/start.sh"
echo "🗑️  To remove all data, run: ./scripts/cleanup.sh"
