#!/bin/bash

###########################################
# XTTS + RVC Voice API Setup Script
# Sets up Python environment and dependencies
###########################################

set -e  # Exit on error

echo "=========================================="
echo "XTTS + RVC Voice API Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${GREEN}Working directory: $SCRIPT_DIR${NC}"
echo ""

###########################################
# Check Python version
###########################################
echo "Step 1: Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

echo -e "${GREEN}✓ Found Python $PYTHON_VERSION${NC}"

# Check if Python version is compatible with TTS
if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 12 ]; then
    echo -e "${RED}Error: Python 3.12+ is not supported by Coqui TTS${NC}"
    echo -e "${YELLOW}TTS requires Python 3.9, 3.10, or 3.11${NC}"
    echo ""
    echo "Please install Python 3.11 and create venv with it:"
    echo "  sudo apt install python3.11 python3.11-venv"
    echo "  python3.11 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install --upgrade pip"
    echo ""
    echo "Then run this script again."
    exit 1
fi

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]; then
    echo -e "${YELLOW}Warning: Python 3.9+ is recommended${NC}"
fi
echo ""

###########################################
# Check for NVIDIA GPU
###########################################
echo "Step 2: Checking for NVIDIA GPU..."
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ NVIDIA GPU detected:${NC}"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    HAS_GPU=true
else
    echo -e "${YELLOW}⚠ No NVIDIA GPU detected. Will use CPU mode.${NC}"
    HAS_GPU=false
fi
echo ""

###########################################
# Create virtual environment
###########################################
echo "Step 3: Creating Python virtual environment..."
if [ -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Removing...${NC}"
    rm -rf .venv
fi

python3 -m venv .venv
echo -e "${GREEN}✓ Virtual environment created${NC}"
echo ""

###########################################
# Activate virtual environment
###########################################
echo "Step 4: Activating virtual environment..."
source .venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

###########################################
# Upgrade pip
###########################################
echo "Step 5: Upgrading pip..."
pip install --upgrade pip
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

###########################################
# Install PyTorch with CUDA support
###########################################
echo "Step 6: Installing PyTorch..."
if [ "$HAS_GPU" = true ]; then
    echo "Installing PyTorch with CUDA 12.1 support..."
    pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
else
    echo "Installing PyTorch (CPU only)..."
    pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu
fi
echo -e "${GREEN}✓ PyTorch installed${NC}"
echo ""

###########################################
# Install requirements
###########################################
echo "Step 7: Installing Python dependencies..."
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

###########################################
# Create required directories
###########################################
echo "Step 8: Creating required directories..."
mkdir -p app/models
mkdir -p data/cache
mkdir -p data/outputs
echo -e "${GREEN}✓ Directories created:${NC}"
echo "  - app/models/ (place RVC models here)"
echo "  - data/cache/ (temporary files)"
echo "  - data/outputs/ (generated audio)"
echo ""

###########################################
# Test GPU availability
###########################################
echo "Step 9: Testing GPU availability..."
python3 << EOF
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
else:
    print("Running in CPU mode")
EOF
echo ""

###########################################
# Test imports
###########################################
echo "Step 10: Testing critical imports..."
python3 << 'EOF'
import sys
errors = []

print("Testing imports...")

try:
    import fastapi
    print("✓ FastAPI")
except ImportError as e:
    errors.append(f"FastAPI: {e}")
    print("✗ FastAPI")

try:
    import uvicorn
    print("✓ Uvicorn")
except ImportError as e:
    errors.append(f"Uvicorn: {e}")
    print("✗ Uvicorn")

try:
    import torch
    print("✓ PyTorch")
except ImportError as e:
    errors.append(f"PyTorch: {e}")
    print("✗ PyTorch")

try:
    from TTS.api import TTS
    print("✓ Coqui TTS")
except ImportError as e:
    errors.append(f"Coqui TTS: {e}")
    print("✗ Coqui TTS")

try:
    import soundfile
    print("✓ SoundFile")
except ImportError as e:
    errors.append(f"SoundFile: {e}")
    print("✗ SoundFile")

try:
    import librosa
    print("✓ Librosa")
except ImportError as e:
    errors.append(f"Librosa: {e}")
    print("✗ Librosa")

if errors:
    print("\n⚠ Some imports failed:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
else:
    print("\n✓ All critical imports successful!")
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}Import test failed. Please check error messages above.${NC}"
    exit 1
fi
echo ""

###########################################
# Check for ffmpeg
###########################################
echo "Step 11: Checking for ffmpeg..."
if command -v ffmpeg &> /dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version | head -n1 | cut -d' ' -f3)
    echo -e "${GREEN}✓ ffmpeg found (version $FFMPEG_VERSION)${NC}"
else
    echo -e "${YELLOW}⚠ ffmpeg not found${NC}"
    echo "ffmpeg is required for audio processing (normalization, effects)"
    echo "Install it with: sudo apt install ffmpeg"
fi
echo ""

###########################################
# Display RVC model instructions
###########################################
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo ""
echo "1. Place your RVC models in app/models/"
echo "   Example structure:"
echo "   app/models/"
echo "   ├── MrCreepyPasta.pth"
echo "   └── MrCreepyPasta.index"
echo ""
echo "2. Start the server:"
echo "   ./start.sh"
echo ""
echo "3. Test the API:"
echo "   ./test_api.sh"
echo ""
echo "4. Access the API at:"
echo "   http://localhost:8001"
echo "   http://localhost:8001/docs (API documentation)"
echo ""
echo -e "${YELLOW}Note:${NC} On first run, XTTS-v2 model will be downloaded (~2GB)"
echo ""

deactivate
