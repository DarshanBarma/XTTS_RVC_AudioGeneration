#!/bin/bash

###########################################
# XTTS + RVC Voice API Start Script
# Activates venv and starts the FastAPI server
###########################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Starting XTTS + RVC Voice API"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: Virtual environment not found${NC}"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if models directory exists
if [ ! -d "app/models" ]; then
    echo -e "${YELLOW}Warning: app/models/ directory not found${NC}"
    echo "Creating directory..."
    mkdir -p app/models
fi

# Check for RVC models
MODEL_COUNT=$(find app/models -name "*.pth" 2>/dev/null | wc -l)
if [ "$MODEL_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠ No RVC models found in app/models/${NC}"
    echo "Place your .pth and .index files there for voice conversion"
else
    echo -e "${GREEN}✓ Found $MODEL_COUNT RVC model(s)${NC}"
fi
echo ""

# Ensure output directories exist
mkdir -p data/cache
mkdir -p data/outputs

# Set environment variables
export PYTHONUNBUFFERED=1

echo "Starting FastAPI server..."
echo "API will be available at:"
echo "  - http://localhost:8001"
echo "  - http://0.0.0.0:8001"
echo "  - http://host.docker.internal:8001 (from Docker)"
echo ""
echo "API Documentation:"
echo "  - http://localhost:8001/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "------------------------------------------"

# Start the server
cd app
python3 main.py
