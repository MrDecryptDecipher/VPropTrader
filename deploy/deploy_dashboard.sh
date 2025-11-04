#!/bin/bash
# Deploy Dashboard to Vercel
# Run from dashboard directory: bash ../deploy/deploy_dashboard.sh

set -e

echo "========================================="
echo "Deploying Dashboard to Vercel"
echo "========================================="

# Check if in dashboard directory
if [ ! -f "package.json" ]; then
    echo "Error: Must run from dashboard directory"
    exit 1
fi

# Install Vercel CLI if not installed
if ! command -v vercel &> /dev/null; then
    echo "Installing Vercel CLI..."
    npm install -g vercel
fi

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo "⚠ WARNING: .env.local not found!"
    echo "Creating from example..."
    cp .env.example .env.local
    echo "Please edit .env.local with your Sidecar URL"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
npm install

# Build locally to test
echo "Building locally..."
npm run build

# Test build
if [ $? -eq 0 ]; then
    echo "✓ Local build successful"
else
    echo "✗ Local build failed"
    exit 1
fi

# Deploy to Vercel
echo ""
echo "Deploying to Vercel..."
echo "Follow the prompts to:"
echo "1. Link to your Vercel account"
echo "2. Set up the project"
echo "3. Configure environment variables"
echo ""

# Production deployment
vercel --prod

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Verify deployment at your Vercel URL"
echo "2. Test WebSocket connection"
echo "3. Check all pages load correctly"
echo ""
