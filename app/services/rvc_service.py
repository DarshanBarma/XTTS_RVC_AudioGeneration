"""
RVC Voice Conversion Service
Provides voice conversion using RVC models with auto-discovery
"""

import os
import gc
import sys
import torch
import logging
import numpy as np
import soundfile as sf
from typing import List, Dict, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RVCService:
    """Service for RVC voice conversion with auto-model discovery"""
    
    def __init__(self, models_dir: str = "app/models"):
        self.models_dir = Path(models_dir)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.loaded_model = None
        self.loaded_model_name = None
        
        # Ensure models directory exists
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs("data/outputs", exist_ok=True)
        
        logger.info(f"RVC Service initialized. Models directory: {self.models_dir}")
        logger.info(f"Using device: {self.device}")
    
    def scan_models(self) -> List[Dict[str, str]]:
        """
        Scan models directory for RVC models (.pth and .index files)
        
        Returns:
            List of model dictionaries with name, pth_path, and index_path
        """
        models = []
        
        if not self.models_dir.exists():
            logger.warning(f"Models directory does not exist: {self.models_dir}")
            return models
        
        # Scan for .pth files
        for pth_file in self.models_dir.rglob("*.pth"):
            model_name = pth_file.stem
            
            # Look for corresponding .index file
            index_file = pth_file.with_suffix(".index")
            
            # Also check in the same directory with the same name
            if not index_file.exists():
                index_file = pth_file.parent / f"{model_name}.index"
            
            model_info = {
                "name": model_name,
                "pth_path": str(pth_file),
                "index_path": str(index_file) if index_file.exists() else None,
                "directory": str(pth_file.parent)
            }
            
            models.append(model_info)
            logger.info(f"Found RVC model: {model_name} at {pth_file}")
        
        return models
    
    def list_models(self) -> List[str]:
        """
        Get list of available RVC model names
        
        Returns:
            List of model names
        """
        models = self.scan_models()
        return [model["name"] for model in models]
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, str]]:
        """
        Get information about a specific model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model info dictionary or None if not found
        """
        models = self.scan_models()
        for model in models:
            if model["name"] == model_name:
                return model
        return None
    
    def load_model(self, model_name: str):
        """
        Load RVC model (placeholder for actual RVC implementation)
        
        Args:
            model_name: Name of the model to load
        """
        # Check if model already loaded
        if self.loaded_model_name == model_name:
            logger.info(f"Model '{model_name}' already loaded")
            return
        
        # Unload previous model
        if self.loaded_model is not None:
            self.unload_model()
        
        model_info = self.get_model_info(model_name)
        if model_info is None:
            raise FileNotFoundError(f"RVC model not found: {model_name}")
        
        logger.info(f"Loading RVC model: {model_name}")
        logger.info(f"PTH file: {model_info['pth_path']}")
        logger.info(f"Index file: {model_info['index_path']}")
        
        # NOTE: This is a placeholder for actual RVC model loading
        # In production, you would load the actual RVC model here:
        # - Load the .pth weights
        # - Load the .index file for voice retrieval
        # - Initialize the RVC inference pipeline
        
        self.loaded_model = model_info  # Placeholder
        self.loaded_model_name = model_name
        
        logger.info(f"RVC model '{model_name}' loaded successfully")
    
    def convert_voice(
        self,
        input_audio_path: str,
        model_name: str,
        pitch_shift: int = 0,
        index_rate: float = 0.75,
        filter_radius: int = 3,
        rms_mix_rate: float = 0.25,
        protect_rate: float = 0.33,
        output_path: Optional[str] = None
    ) -> str:
        """
        Convert voice using RVC model
        
        Args:
            input_audio_path: Path to input audio file
            model_name: Name of RVC model to use
            pitch_shift: Pitch shift in semitones (-12 to 12)
            index_rate: Feature retrieval ratio (0.0 to 1.0)
            filter_radius: Median filtering radius (0 to 7)
            rms_mix_rate: Volume envelope mix rate (0.0 to 1.0)
            protect_rate: Protect voiceless consonants (0.0 to 0.5)
            output_path: Output file path
            
        Returns:
            Path to converted audio file
        """
        try:
            # Validate input
            if not os.path.exists(input_audio_path):
                raise FileNotFoundError(f"Input audio not found: {input_audio_path}")
            
            # Load model if needed
            self.load_model(model_name)
            
            # Generate output path
            if output_path is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"data/outputs/rvc_{model_name}_{timestamp}.wav"
            
            logger.info(f"Converting voice: {input_audio_path} -> {model_name}")
            logger.info(f"Parameters: pitch={pitch_shift}, index_rate={index_rate}")
            
            # NOTE: This is a placeholder for actual RVC inference
            # In production, you would implement:
            # 1. Load and preprocess audio
            # 2. Extract features
            # 3. Apply RVC conversion
            # 4. Apply pitch shifting
            # 5. Mix with original using rms_mix_rate
            # 6. Save output
            
            # For now, we'll copy the input as a placeholder
            import shutil
            shutil.copy(input_audio_path, output_path)
            
            logger.warning("RVC inference not fully implemented - using placeholder")
            logger.info(f"Voice conversion completed: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error during voice conversion: {e}")
            raise RuntimeError(f"Voice conversion failed: {e}")
        
        finally:
            # Clear GPU cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    def unload_model(self):
        """Unload model and free GPU memory"""
        if self.loaded_model is not None:
            logger.info(f"Unloading RVC model: {self.loaded_model_name}")
            del self.loaded_model
            self.loaded_model = None
            self.loaded_model_name = None
            
        # Clear GPU cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()
            logger.info("GPU memory cleared")
    
    def is_model_loaded(self) -> bool:
        """Check if a model is loaded"""
        return self.loaded_model is not None
    
    def get_loaded_model_name(self) -> Optional[str]:
        """Get name of currently loaded model"""
        return self.loaded_model_name
    
    def get_device_info(self) -> dict:
        """Get device information"""
        info = {
            "device": self.device,
            "model_loaded": self.is_model_loaded(),
            "loaded_model": self.loaded_model_name
        }
        
        if torch.cuda.is_available():
            info.update({
                "gpu_name": torch.cuda.get_device_name(0),
                "gpu_memory_allocated": f"{torch.cuda.memory_allocated(0) / 1024**3:.2f} GB",
                "gpu_memory_reserved": f"{torch.cuda.memory_reserved(0) / 1024**3:.2f} GB",
            })
        
        return info


# Singleton instance
_rvc_service = None

def get_rvc_service() -> RVCService:
    """Get or create RVC service singleton"""
    global _rvc_service
    if _rvc_service is None:
        _rvc_service = RVCService()
    return _rvc_service

