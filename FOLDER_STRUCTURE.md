# Voice_API Folder Structure

```
Voice_API/
│
├── .git/                           # Git repository
├── .gitignore                      # Git ignore configuration
├── .venv/                          # Python virtual environment
│
├── requirements.txt                # Python dependencies
├── setup.sh                        # Setup script for environment
├── start.sh                        # Server startup script
├── test_api.sh                     # API testing script
│
├── app/                            # Main application directory
│   ├── main.py                     # FastAPI application entry point
│   │
│   ├── models/                     # RVC voice models
│   │   ├── MrCreepyPasta.pth      # RVC model weights
│   │   └── MrCreepyPasta.index    # RVC model index file
│   │
│   ├── services/                   # Service layer
│   │   ├── __init__.py            # Services package initialization
│   │   ├── __pycache__/           # Python cache
│   │   ├── rvc_service.py         # RVC voice conversion service
│   │   └── xtts_service.py        # XTTS text-to-speech service
│   │
│   └── utils/                      # Utility functions
│       ├── __init__.py            # Utils package initialization
│       ├── __pycache__/           # Python cache
│       └── audio_processor.py     # Audio processing utilities
│
└── data/                           # Data storage directory
    ├── cache/                      # Temporary cache files
    └── outputs/                    # Generated audio outputs
```

## File Descriptions

### Root Directory
- **`.gitignore`** - Specifies files/folders to ignore in git (venv, cache, models, etc.)
- **`requirements.txt`** - Python package dependencies
- **`setup.sh`** - Automated setup script for environment and dependencies
- **`start.sh`** - Script to start the FastAPI server
- **`test_api.sh`** - Script to test all API endpoints

### app/
- **`main.py`** - FastAPI application with endpoints for TTS and RVC conversion

### app/models/
- **`MrCreepyPasta.pth`** - Pre-trained RVC model weights
- **`MrCreepyPasta.index`** - FAISS index for voice conversion

### app/services/
- **`xtts_service.py`** - Service for XTTS-v2 text-to-speech generation
- **`rvc_service.py`** - Service for RVC voice conversion/cloning

### app/utils/
- **`audio_processor.py`** - Audio processing utilities (normalization, effects, etc.)

### data/
- **`cache/`** - Temporary files during processing
- **`outputs/`** - Final generated audio files

## Key Technologies
- **FastAPI** - Web framework
- **XTTS-v2** - Text-to-speech generation
- **RVC (Retrieval-based Voice Conversion)** - Voice cloning/conversion
- **PyTorch** - Deep learning framework
- **FAISS** - Vector similarity search
