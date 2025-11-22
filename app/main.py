"""
XTTS + RVC Voice Generation API
FastAPI server for text-to-speech and voice conversion
"""

import os
import gc
import uuid
import logging
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from services.xtts_service import get_xtts_service
from services.rvc_service import get_rvc_service
from utils.audio_processor import get_audio_processor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="XTTS + RVC Voice Generation API",
    description="Text-to-speech with optional voice conversion using XTTS-v2 and RVC",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
xtts_service = get_xtts_service()
rvc_service = get_rvc_service()
audio_processor = get_audio_processor()


# Request/Response Models
class GenerateSpeechRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    language: str = Field(default="en", description="Language code (en, es, fr, de, etc.)")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed (0.5 to 2.0)")
    rvc_model: Optional[str] = Field(default=None, description="RVC model name for voice conversion")
    pitch_shift: int = Field(default=0, ge=-12, le=12, description="Pitch shift in semitones")
    normalize: bool = Field(default=True, description="Normalize audio levels")


class BatchGenerateRequest(BaseModel):
    texts: List[str] = Field(..., min_items=1, max_items=50)
    language: str = Field(default="en")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    rvc_model: Optional[str] = None
    pitch_shift: int = Field(default=0, ge=-12, le=12)


class GenerateSpeechResponse(BaseModel):
    status: str
    audio_id: str
    download_url: str
    duration: Optional[float] = None
    processing_time: Optional[float] = None


class HealthResponse(BaseModel):
    status: str
    xtts_loaded: bool
    rvc_loaded: bool
    gpu_info: dict


class RVCModelInfo(BaseModel):
    name: str
    pth_path: str
    index_path: Optional[str]
    directory: str


# API Endpoints
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "XTTS + RVC Voice Generation API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "generate_speech": "POST /generate-speech",
            "batch_generate": "POST /batch-generate",
            "download": "GET /download/{audio_id}",
            "health": "GET /health",
            "list_models": "GET /list-rvc-models"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health and status"""
    try:
        gpu_info = xtts_service.get_device_info()
        
        return HealthResponse(
            status="healthy",
            xtts_loaded=xtts_service.is_model_loaded(),
            rvc_loaded=rvc_service.is_model_loaded(),
            gpu_info=gpu_info
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/list-rvc-models")
async def list_rvc_models():
    """List available RVC models"""
    try:
        models = rvc_service.scan_models()
        
        return {
            "status": "success",
            "count": len(models),
            "models": models
        }
    except Exception as e:
        logger.error(f"Error listing RVC models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-speech", response_model=GenerateSpeechResponse)
async def generate_speech(request: GenerateSpeechRequest):
    """
    Generate speech from text with optional RVC voice conversion
    
    This endpoint:
    1. Generates speech using XTTS-v2
    2. Optionally converts voice using RVC model
    3. Optionally normalizes audio
    4. Returns audio ID for download
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Generating speech: {len(request.text)} chars, lang={request.language}")
        
        # Generate unique audio ID
        audio_id = audio_processor.generate_audio_id()
        
        # Step 1: Generate speech with XTTS
        xtts_output_path = audio_processor.get_audio_path(audio_id, "xtts")
        
        xtts_service.generate_speech(
            text=request.text,
            language=request.language,
            speed=request.speed,
            output_path=xtts_output_path
        )
        
        current_audio_path = xtts_output_path
        
        # Step 2: Apply RVC voice conversion if requested
        if request.rvc_model:
            logger.info(f"Applying RVC model: {request.rvc_model}")
            
            rvc_output_path = audio_processor.get_audio_path(audio_id, "rvc")
            
            current_audio_path = rvc_service.convert_voice(
                input_audio_path=current_audio_path,
                model_name=request.rvc_model,
                pitch_shift=request.pitch_shift,
                output_path=rvc_output_path
            )
        
        # Step 3: Normalize audio if requested
        if request.normalize:
            logger.info("Normalizing audio")
            final_output_path = audio_processor.get_audio_path(audio_id, "final")
            
            current_audio_path = audio_processor.normalize_audio(
                input_path=current_audio_path,
                output_path=final_output_path
            )
        
        # Get audio duration
        duration = audio_processor.get_audio_duration(current_audio_path)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Speech generation complete: {audio_id} ({processing_time:.2f}s)")
        
        # Clean up VRAM
        if request.rvc_model:
            rvc_service.unload_model()
        
        return GenerateSpeechResponse(
            status="success",
            audio_id=audio_id,
            download_url=f"/download/{audio_id}",
            duration=duration,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error generating speech: {e}")
        raise HTTPException(status_code=500, detail=f"Speech generation failed: {str(e)}")
    
    finally:
        # Ensure VRAM is cleared
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()


@app.post("/batch-generate")
async def batch_generate(request: BatchGenerateRequest, background_tasks: BackgroundTasks):
    """
    Generate multiple audio files in batch
    
    Returns list of audio IDs for each text
    """
    try:
        logger.info(f"Batch generation: {len(request.texts)} texts")
        
        results = []
        
        for idx, text in enumerate(request.texts):
            try:
                audio_id = audio_processor.generate_audio_id()
                
                # Generate XTTS
                output_path = audio_processor.get_audio_path(audio_id, "batch")
                
                xtts_service.generate_speech(
                    text=text,
                    language=request.language,
                    speed=request.speed,
                    output_path=output_path
                )
                
                current_path = output_path
                
                # Apply RVC if requested
                if request.rvc_model:
                    rvc_output = audio_processor.get_audio_path(audio_id, "batch_rvc")
                    current_path = rvc_service.convert_voice(
                        input_audio_path=current_path,
                        model_name=request.rvc_model,
                        pitch_shift=request.pitch_shift,
                        output_path=rvc_output
                    )
                
                results.append({
                    "index": idx,
                    "status": "success",
                    "audio_id": audio_id,
                    "download_url": f"/download/{audio_id}",
                    "text_preview": text[:50] + "..." if len(text) > 50 else text
                })
                
                logger.info(f"Batch {idx + 1}/{len(request.texts)} complete")
                
            except Exception as e:
                logger.error(f"Batch item {idx} failed: {e}")
                results.append({
                    "index": idx,
                    "status": "error",
                    "error": str(e),
                    "text_preview": text[:50] + "..." if len(text) > 50 else text
                })
        
        # Clean up models
        if request.rvc_model:
            rvc_service.unload_model()
        
        return {
            "status": "completed",
            "total": len(request.texts),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "error"]),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Batch generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{audio_id}")
async def download_audio(audio_id: str):
    """
    Download generated audio file by ID
    
    Searches for audio files with the given ID and returns the most recent one
    """
    try:
        # Look for files with this audio_id
        possible_prefixes = ["final", "rvc", "xtts", "batch_rvc", "batch", "audio"]
        
        for prefix in possible_prefixes:
            file_path = audio_processor.get_audio_path(audio_id, prefix)
            
            if os.path.exists(file_path):
                logger.info(f"Serving audio file: {file_path}")
                return FileResponse(
                    file_path,
                    media_type="audio/wav",
                    filename=f"{audio_id}.wav"
                )
        
        # File not found
        logger.warning(f"Audio file not found: {audio_id}")
        raise HTTPException(status_code=404, detail=f"Audio file not found: {audio_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/supported-languages")
async def get_supported_languages():
    """Get list of supported languages for XTTS"""
    return {
        "languages": xtts_service.get_supported_languages(),
        "count": len(xtts_service.get_supported_languages())
    }


@app.post("/cleanup")
async def cleanup_old_files(max_age_hours: int = 24):
    """Clean up old audio files"""
    try:
        audio_processor.cleanup_old_files(max_age_hours)
        return {"status": "success", "message": f"Cleaned up files older than {max_age_hours} hours"}
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("=" * 50)
    logger.info("XTTS + RVC Voice Generation API Starting...")
    logger.info("=" * 50)
    
    # Pre-load XTTS model
    try:
        logger.info("Pre-loading XTTS model...")
        xtts_service.load_model()
        logger.info("XTTS model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to pre-load XTTS model: {e}")
    
    # Scan for RVC models
    try:
        models = rvc_service.list_models()
        logger.info(f"Found {len(models)} RVC models: {models}")
    except Exception as e:
        logger.error(f"Failed to scan RVC models: {e}")
    
    logger.info("API startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    logger.info("Shutting down API...")
    
    # Unload models
    xtts_service.unload_model()
    rvc_service.unload_model()
    
    logger.info("API shutdown complete")


# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )

