#!/bin/bash

# Music Tools API - Port Conflict Resolution Script
# This script helps resolve common port conflicts when starting the service

set -e

echo "🔧 Music Tools API - Port Conflict Resolver"
echo "==========================================="
echo ""

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to find process using port
find_process() {
    local port=$1
    lsof -Pi :$port -sTCP:LISTEN
}

# Function to suggest alternative ports
suggest_alternative() {
    local base_port=$1
    local service_name=$2
    
    echo "🔍 Finding alternative port for $service_name (base: $base_port)..."
    
    for i in {1..10}; do
        local alt_port=$((base_port + i))
        if ! check_port $alt_port; then
            echo "✅ Suggested alternative port: $alt_port"
            return $alt_port
        fi
    done
    
    echo "❌ Could not find alternative port in range $((base_port + 1))-$((base_port + 10))"
    return 1
}

echo "🔍 Checking for port conflicts..."
echo ""

# Check API port (8000/8001)
if check_port 8000; then
    echo "⚠️  Port 8000 (API) is already in use:"
    find_process 8000
    echo ""
    if ! check_port 8001; then
        echo "✅ Port 8001 is available as alternative"
        echo "💡 Docker is already configured to use port 8001 externally"
        echo "   Just run: docker-compose up -d"
    else
        suggest_alternative 8001 "API"
        api_alt=$?
        echo "💡 Update docker-compose.yml ports section to: \"$api_alt:8000\""
    fi
    echo ""
else
    echo "✅ Port 8000 (API) is available"
    echo "💡 You can change docker-compose.yml back to \"8000:8000\" if preferred"
fi

# Check Redis port (6379)
if check_port 6379; then
    echo "⚠️  Port 6379 (Redis) is already in use:"
    find_process 6379
    echo ""
    echo "🔧 Solutions for Redis port conflict:"
    echo ""
    echo "Option 1: Use existing Redis instance"
    echo "  - Update .env file:"
    echo "    REDIS_URL=redis://localhost:6379/0"
    echo "  - Remove Redis from docker-compose.yml or use:"
    echo "    docker-compose up -d music-tools-api"
    echo ""
    echo "Option 2: Use different port for Docker Redis"
    echo "  - Docker Redis is already configured to use port 6380 externally"
    echo "  - Update .env file:"
    echo "    REDIS_URL=redis://localhost:6380/0"
    echo "  - Start with: docker-compose up -d"
    echo ""
    echo "Option 3: Stop existing Redis"
    echo "  - If you don't need the existing Redis:"
    echo "    sudo systemctl stop redis-server  # Linux"
    echo "    brew services stop redis         # macOS"
    echo ""
else
    echo "✅ Port 6379 (Redis) is available"
fi

# Check Nginx ports (80, 443) if using production profile
if check_port 80; then
    echo "⚠️  Port 80 (HTTP) is already in use:"
    find_process 80
    echo "💡 This affects the production Nginx setup"
    echo ""
fi

if check_port 443; then
    echo "⚠️  Port 443 (HTTPS) is already in use:"
    find_process 443
    echo "💡 This affects the production Nginx setup"
    echo ""
fi

echo ""
echo "🚀 Quick Start Options:"
echo ""

if ! check_port 8001 && ! check_port 6379; then
    echo "✅ All ports available - you can start normally:"
    echo "   docker-compose up -d"
    echo "   API will be available on: http://localhost:8001"
elif ! check_port 8001 && check_port 6379; then
    echo "✅ API port 8001 available, Redis port in use:"
    echo ""
    echo "Option A: Use Docker Redis on port 6380"
    echo "   1. Update .env: REDIS_URL=redis://localhost:6380/0"
    echo "   2. Run: docker-compose up -d"
    echo ""
    echo "Option B: Use existing Redis"
    echo "   1. Update .env: REDIS_URL=redis://localhost:6379/0"
    echo "   2. Run: docker-compose up -d music-tools-api"
    echo ""
    echo "Option C: Stop existing Redis and use Docker"
    echo "   1. sudo systemctl stop redis-server  # or brew services stop redis"
    echo "   2. Update docker-compose.yml to use port 6379:6379"
    echo "   3. Run: docker-compose up -d"
else
    echo "⚠️  Multiple port conflicts detected"
    echo "   Please resolve port conflicts manually or use alternative ports"
fi

echo ""
echo "📝 Configuration Files to Update:"
echo "   .env file - for Redis and API configuration"
echo "   docker-compose.yml - for Docker port mappings"
echo ""
echo "🔍 Useful Commands:"
echo "   Check what's using a port: lsof -i :PORT_NUMBER"
echo "   Stop Docker services: docker-compose down"
echo "   View Docker logs: docker-compose logs"
echo "   Check Docker status: docker-compose ps"
echo ""
echo "💡 Need help? Check INSTALLATION.md for detailed troubleshooting"
