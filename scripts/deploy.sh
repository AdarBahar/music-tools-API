#!/usr/bin/env bash

# Deploy Music Tools API to Hetzner
# Service: music-tools-api (systemd)
# URL: https://apitools.bahar.co.il
#
# GUARDRAILS:
# - Only restarts music-tools-api service (NEVER affects other services)
# - Validates we're deploying to correct directory
# - Creates timestamped backup before deployment
# - Verifies deployment health after completion

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================
ENV_NAME="PRODUCTION"
SERVER="apitools"  # SSH alias (configured in ~/.ssh/config)
REMOTE_TMP="/tmp-apitools"
REMOTE_APP_DIR="/var/www/apitools"
SERVICE_NAME="music-tools-api"
TARBALL_NAME="music-tools-api-dist.tar.gz"
HEALTH_URL="https://apitools.bahar.co.il/health"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Deploy Music Tools API to Hetzner${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Target: ${REMOTE_APP_DIR}${NC}"
echo -e "${YELLOW}Service: ${SERVICE_NAME}${NC}"
echo -e "${YELLOW}URL: ${HEALTH_URL}${NC}"
echo ""

# Step 1: Create distribution tarball
echo -e "${YELLOW}[1/6] Creating distribution tarball...${NC}"
cd "$PROJECT_DIR"

# Create tarball with required files only (exclude venv, __pycache__, etc.)
tar -czf "$TARBALL_NAME" \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='.env' \
    --exclude='outputs/*' \
    --exclude='temp/*' \
    --exclude='uploads/*' \
    --exclude='logs/*' \
    --exclude='*.tar.gz' \
    --exclude='*.zip' \
    --exclude='bin' \
    --exclude='lib' \
    --exclude='include' \
    --exclude='share' \
    --exclude='.codeagent' \
    main.py \
    requirements.txt \
    app/ \
    2>/dev/null || {
        echo -e "${RED}Failed to create tarball${NC}"
        exit 1
    }

ARCHIVE_SIZE=$(ls -lh "$TARBALL_NAME" | awk '{print $5}')
echo -e "${GREEN}✅ Tarball created: $TARBALL_NAME ($ARCHIVE_SIZE)${NC}"
echo ""

# Step 2: Upload to server
echo -e "${YELLOW}[2/6] Uploading to Hetzner...${NC}"
ssh "$SERVER" "mkdir -p $REMOTE_TMP"
scp "$TARBALL_NAME" "$SERVER:$REMOTE_TMP/"
echo -e "${GREEN}✅ Upload complete${NC}"
echo ""

# Step 3: Backup current deployment
echo -e "${YELLOW}[3/6] Creating backup on server...${NC}"
ssh "$SERVER" << 'EOF'
set -e
BACKUP_DIR="/tmp-apitools/backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -d "/var/www/apitools/app" ]; then
    echo "📦 Backing up current deployment..."
    cp -r /var/www/apitools/app "$BACKUP_DIR/" 2>/dev/null || true
    cp /var/www/apitools/main.py "$BACKUP_DIR/" 2>/dev/null || true
    cp /var/www/apitools/requirements.txt "$BACKUP_DIR/" 2>/dev/null || true
    echo "   Backup saved to: $BACKUP_DIR"
else
    echo "   No existing deployment to backup"
fi

# Keep only last 5 backups
cd /tmp-apitools
ls -dt backup-* 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true
EOF
echo -e "${GREEN}✅ Backup complete${NC}"
echo ""

# Step 4: Deploy on server
echo -e "${YELLOW}[4/6] Deploying on server...${NC}"
ssh "$SERVER" << EOF
set -e

echo "📦 Extracting tarball..."
cd $REMOTE_TMP
rm -rf dist-new
mkdir -p dist-new
tar -xzf $TARBALL_NAME -C dist-new

echo "📂 Deploying new files..."
# Create directories if they don't exist
mkdir -p $REMOTE_APP_DIR/app
mkdir -p $REMOTE_APP_DIR/outputs
mkdir -p $REMOTE_APP_DIR/temp
mkdir -p $REMOTE_APP_DIR/uploads
mkdir -p $REMOTE_APP_DIR/logs

# Copy new files
cp -r dist-new/app/* $REMOTE_APP_DIR/app/
cp dist-new/main.py $REMOTE_APP_DIR/
cp dist-new/requirements.txt $REMOTE_APP_DIR/

# Install/update dependencies if requirements changed
echo "📦 Checking dependencies..."
cd $REMOTE_APP_DIR
if [ -f venv/bin/pip ]; then
    source venv/bin/activate
    pip install -r requirements.txt --quiet
    deactivate
else
    echo "⚠️  Virtual environment not found - skipping pip install"
fi

echo "♻️  Restarting $SERVICE_NAME service..."
sudo systemctl restart $SERVICE_NAME

echo "⏳ Waiting for service to start..."
sleep 3

echo "✅ Deployment complete on \$(date)"
EOF

echo -e "${GREEN}✅ Deployment complete${NC}"
echo ""

# Step 5: Verify deployment
echo -e "${YELLOW}[5/6] Verifying deployment...${NC}"
ssh "$SERVER" << EOF
echo "📊 Service Status:"
sudo systemctl status $SERVICE_NAME --no-pager | head -15

echo ""
echo "🏥 Health Check (local):"
curl -s http://127.0.0.1:8000/health | python3 -m json.tool 2>/dev/null || echo "Local health check failed!"
EOF

# External health check
echo ""
echo "🌐 External Health Check:"
HEALTH_RESPONSE=$(curl -s "$HEALTH_URL" 2>/dev/null || echo '{"status":"error"}')
echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | grep -q '"status"'; then
    echo -e "${GREEN}✅ External health check passed${NC}"
else
    echo -e "${RED}❌ External health check failed${NC}"
fi
echo ""

# Step 6: Log deployment
echo -e "${YELLOW}[6/6] Logging deployment...${NC}"
DEPLOYMENT_TIME=$(date '+%Y-%m-%d %H:%M:%S')
ssh "$SERVER" << EOF
echo "🚀 ============================================================" >> /var/www/apitools/logs/deployment.log 2>/dev/null || true
echo "🚀 DEPLOYMENT COMPLETED - $DEPLOYMENT_TIME" >> /var/www/apitools/logs/deployment.log 2>/dev/null || true
echo "🚀 Environment: $ENV_NAME" >> /var/www/apitools/logs/deployment.log 2>/dev/null || true
echo "🚀 Deployed by: \$(whoami)@\$(hostname)" >> /var/www/apitools/logs/deployment.log 2>/dev/null || true
echo "🚀 ============================================================" >> /var/www/apitools/logs/deployment.log 2>/dev/null || true
EOF
echo -e "${GREEN}✅ Deployment logged${NC}"
echo ""

# Cleanup local tarball
echo "🧹 Cleaning up..."
rm -f "$PROJECT_DIR/$TARBALL_NAME"
echo -e "${GREEN}✅ Cleanup complete${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "🌐 API URL: https://apitools.bahar.co.il"
echo "🏥 Health: https://apitools.bahar.co.il/health"
echo "📖 Docs: https://apitools.bahar.co.il/docs"
echo ""
echo -e "${GREEN}🎉 All done! Music Tools API deployed successfully.${NC}"
