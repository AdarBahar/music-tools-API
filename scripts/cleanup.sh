#!/bin/bash

# Music Tools API - Cleanup Script

set -e

echo "🧹 Music Tools API Cleanup"
echo ""

# Warning
echo "⚠️  WARNING: This will remove all data and Docker resources!"
echo "   - All uploaded files will be deleted"
echo "   - All converted audio files will be deleted"
echo "   - All Docker containers and volumes will be removed"
echo ""

read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cleanup cancelled."
    exit 1
fi

echo "🛑 Stopping services..."
docker-compose down -v --remove-orphans

echo "🗑️  Removing data directories..."
rm -rf data/

echo "🐳 Removing Docker images..."
docker-compose down --rmi all

echo "🧽 Removing unused Docker resources..."
docker system prune -f

echo "✅ Cleanup completed!"
echo ""
echo "💡 To start fresh, run: ./scripts/start.sh"
