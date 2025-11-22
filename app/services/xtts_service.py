"""
XTTS-v2 Text-to-Speech Service
Provides multilingual TTS generation with GPU memory optimization
"""

import os
import gc
import torch
import logging
from typing import Optional
from TTS.api import TTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class XTTSService:
    """Service for XTTS-v2 text-to-speech generation"""
    
    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        self.cache_dir = "data/cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs("data/outputs", exist_ok=True)
        logger.info(f"XTTS Service initialized. Using device: {self.device}")
        
    def load_model(self):
        """Load XTTS-v2 model into memory"""
        if self.model is None:
            try:
                logger.info(f"Loading XTTS-v2 model: {self.model_name}")
                self.model = TTS(self.model_name).to(self.device)
                logger.info("XTTS-v2 model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load XTTS model: {e}")
                raise RuntimeError(f"Failed to load XTTS model: {e}")
    
    def unload_model(self):
        """Free VRAM"""
        if self.model is not None:
            logger.info("Unloading XTTS model and clearing VRAM")
            del self.model
            self.model = None
            
        # Clear GPU cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()
            logger.info("GPU memory cleared")
    
    def generate_speech(
        self,
        text: str,
        language: str = "en",
        speaker_wav: Optional[str] = None,
        speed: float = 1.0,
        output_path: str = None
    ) -> str:
        """
        Generate speech from text using XTTS-v2
        
        Args:
            text: Text to convert to speech
            language: Language code (en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, ja, hu, ko)
            speaker_wav: Optional path to reference audio for voice cloning
            speed: Speech speed (0.5 to 2.0)
            output_path: Path to save the generated audio
            
        Returns:
            Path to the generated audio file
        """
        try:
            # Load model if not already loaded
            self.load_model()
            
            # Validate language
            supported_languages = [
                "en", "es", "fr", "de", "it", "pt", "pl", "tr", 
                "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"
            ]
            if language not in supported_languages:
                logger.warning(f"Language '{language}' not in supported list, defaulting to 'en'")
                language = "en"
            
            # Ensure output path
            if output_path is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"data/outputs/xtts_{timestamp}.wav"
            
            logger.info(f"Generating speech: {len(text)} chars, lang={language}, speed={speed}")
            
            # Generate speech
            if speaker_wav and os.path.exists(speaker_wav):
                # Voice cloning mode
                self.model.tts_to_file(
                    text=text,
                    speaker_wav=speaker_wav,
                    language=language,
                    file_path=output_path,
                    speed=speed
                )
            else:
                # Default voice mode
                self.model.tts_to_file(
                    text=text,
                    language=language,
                    file_path=output_path,
                    speed=speed
                )
            
            logger.info(f"Speech generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            raise RuntimeError(f"Failed to generate speech: {e}")
        
        finally:
            # Clear cache after generation to free VRAM
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        return [
            "en", "es", "fr", "de", "it", "pt", "pl", "tr",
            "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"
        ]
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None
    
    def get_device_info(self) -> dict:
        """Get device information"""
        info = {
            "device": self.device,
            "model_loaded": self.is_model_loaded()
        }
        
        if torch.cuda.is_available():
            info.update({
                "gpu_name": torch.cuda.get_device_name(0),
                "gpu_memory_allocated": f"{torch.cuda.memory_allocated(0) / 1024**3:.2f} GB",
                "gpu_memory_reserved": f"{torch.cuda.memory_reserved(0) / 1024**3:.2f} GB",
                "gpu_memory_total": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB"
            })
        
        return info


# Singleton instance
_xtts_service = None

def get_xtts_service() -> XTTSService:
    """Get or create XTTS service singleton"""
    global _xtts_service
    if _xtts_service is None:
        _xtts_service = XTTSService()
    return _xtts_service

