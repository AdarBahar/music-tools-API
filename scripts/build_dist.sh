#!/bin/bash
# Build script for Music Tools API deployment package
set -e

# Clean previous build
rm -rf dist
mkdir dist

# Copy source code and essentials
cp -r app main.py requirements.txt dist/

# Copy config and docs if needed
[ -f pyproject.toml ] && cp pyproject.toml dist/
[ -f setup.py ] && cp setup.py dist/
[ -f .env ] && cp .env dist/
[ -d scripts ] && cp -r scripts dist/
[ -d outputs ] && cp -r outputs dist/
[ -d uploads ] && cp -r uploads dist/
[ -d examples ] && cp -r examples dist/
[ -d docs ] && cp -r docs dist/

# Remove __pycache__ and .DS_Store
find dist/ -type d -name '__pycache__' -exec rm -rf {} +
find dist/ -name '*.pyc' -delete
find dist/ -name '.DS_Store' -delete

# Create zip file
cd dist
zip -r ../music-tools-api-dist.zip .
cd ..

echo "Build complete: music-tools-api-dist.zip created."
