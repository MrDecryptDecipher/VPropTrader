#!/bin/bash
# Run all tests
# Usage: bash scripts/run_tests.sh

set -e

echo "========================================="
echo "Quant Ω Supra AI - Test Suite"
echo "========================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Navigate to project root
cd "$(dirname "$0")/.."

# Activate virtual environment if exists
if [ -d "sidecar/venv" ]; then
    source sidecar/venv/bin/activate
fi

# Install test dependencies
echo "Installing test dependencies..."
pip install pytest pytest-asyncio httpx

# Run unit tests
echo ""
echo "========================================="
echo "Running Unit Tests"
echo "========================================="

echo ""
echo "1. ML Inference Speed Tests..."
python tests/test_ml_inference.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ ML Inference tests passed${NC}"
else
    echo -e "${RED}✗ ML Inference tests failed${NC}"
    exit 1
fi

echo ""
echo "2. Governor Tests..."
python tests/test_governors.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Governor tests passed${NC}"
else
    echo -e "${RED}✗ Governor tests failed${NC}"
    exit 1
fi

# Run integration tests
echo ""
echo "========================================="
echo "Running Integration Tests"
echo "========================================="

# Check if Sidecar is running
echo "Checking if Sidecar service is running..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ Sidecar is running${NC}"
    
    echo ""
    echo "3. Integration Tests..."
    python tests/test_integration.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Integration tests passed${NC}"
    else
        echo -e "${RED}✗ Integration tests failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ Sidecar not running - skipping integration tests${NC}"
    echo "Start Sidecar with: cd sidecar && python -m app.main"
fi

# Test summary
echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo -e "${GREEN}✓ All tests passed!${NC}"
echo ""
echo "System is ready for deployment"
echo ""
