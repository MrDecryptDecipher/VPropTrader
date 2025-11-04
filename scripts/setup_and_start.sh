#!/bin/bash
# Automated Setup and Start Script
# This script sets up everything and starts the Sidecar service

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Quant Ω Supra AI - Automated Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SIDECAR_DIR="$PROJECT_ROOT/sidecar"

echo -e "${BLUE}Project Root:${NC} $PROJECT_ROOT"
echo -e "${BLUE}Sidecar Dir:${NC} $SIDECAR_DIR"
echo ""

# Check Python
echo -e "${BLUE}Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} Found: $PYTHON_VERSION"
else
    echo -e "${YELLOW}✗ Python 3 not found${NC}"
    exit 1
fi
echo ""

# Check Redis
echo -e "${BLUE}Checking Redis...${NC}"
if redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✓${NC} Redis is running"
else
    echo -e "${YELLOW}⚠ Redis not running, attempting to start...${NC}"
    sudo systemctl start redis-server || echo "Could not start Redis"
fi
echo ""

# Navigate to sidecar directory
cd "$SIDECAR_DIR"

# Check if venv exists
if [ -d "venv" ]; then
    echo -e "${GREEN}✓${NC} Virtual environment exists"
else
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
fi
echo ""

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓${NC} Virtual environment activated"
echo ""

# Upgrade pip
echo -e "${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip --quiet
echo -e "${GREEN}✓${NC} Pip upgraded"
echo ""

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
echo -e "${YELLOW}This may take 2-3 minutes...${NC}"
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓${NC} Dependencies installed"
echo ""

# Check .env file
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} Configuration file (.env) exists"
    
    # Show MT5 credentials
    echo -e "${BLUE}MT5 Configuration:${NC}"
    grep "MT5_LOGIN" .env
    grep "MT5_SERVER" .env
else
    echo -e "${YELLOW}⚠ .env file not found${NC}"
    echo "Copying from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env with your credentials${NC}"
    exit 1
fi
echo ""

# Create necessary directories
echo -e "${BLUE}Creating directories...${NC}"
mkdir -p data logs models
echo -e "${GREEN}✓${NC} Directories created"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${BLUE}Starting Sidecar Service...${NC}"
echo ""

# Start the service
python -m app.main
