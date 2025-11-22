"""
Audio Processing Utilities
Handles audio file management, format conversion, and processing
"""

import os
import uuid
import logging
import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioProcessor:
    """Utility class for audio file processing and management"""
    
    def __init__(self, output_dir: str = "data/outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"AudioProcessor initialized. Output directory: {self.output_dir}")
    
    def generate_audio_id(self) -> str:
        """Generate unique audio ID"""
        return str(uuid.uuid4())
    
    def get_audio_path(self, audio_id: str, prefix: str = "audio") -> str:
        """
        Get path for audio file
        
        Args:
            audio_id: Unique audio identifier
            prefix: File prefix
            
        Returns:
            Full path to audio file
        """
        return str(self.output_dir / f"{prefix}_{audio_id}.wav")
    
    def list_audio_files(self) -> list:
        """
        List all audio files in output directory
        
        Returns:
            List of audio file paths
        """
        return [str(f) for f in self.output_dir.glob("*.wav")]
    
    def file_exists(self, audio_id: str, prefix: str = "audio") -> bool:
        """
        Check if audio file exists
        
        Args:
            audio_id: Audio identifier
            prefix: File prefix
            
        Returns:
            True if file exists
        """
        path = self.get_audio_path(audio_id, prefix)
        return os.path.exists(path)
    
    def normalize_audio(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        target_lufs: float = -16.0
    ) -> str:
        """
        Normalize audio levels using ffmpeg
        
        Args:
            input_path: Path to input audio
            output_path: Path to output audio (auto-generated if None)
            target_lufs: Target loudness in LUFS
            
        Returns:
            Path to normalized audio
        """
        try:
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"normalized_{timestamp}.wav")
            
            logger.info(f"Normalizing audio: {input_path}")
            
            cmd = [
                "ffmpeg", "-i", input_path,
                "-af", f"loudnorm=I={target_lufs}:LRA=11:TP=-1.5",
                "-ar", "44100",
                "-y",
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            
            logger.info(f"Audio normalized successfully: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg normalization failed: {e.stderr}")
            logger.warning("Returning original audio without normalization")
            return input_path
        except FileNotFoundError:
            logger.error("FFmpeg not found. Please install ffmpeg.")
            return input_path
    
    def convert_format(
        self,
        input_path: str,
        output_format: str = "wav",
        sample_rate: int = 44100
    ) -> str:
        """
        Convert audio to different format
        
        Args:
            input_path: Path to input audio
            output_format: Target format (wav, mp3, ogg, etc.)
            sample_rate: Target sample rate
            
        Returns:
            Path to converted audio
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.output_dir / f"converted_{timestamp}.{output_format}")
            
            logger.info(f"Converting audio to {output_format}: {input_path}")
            
            cmd = [
                "ffmpeg", "-i", input_path,
                "-ar", str(sample_rate),
                "-y",
                output_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            logger.info(f"Audio converted successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Format conversion failed: {e}")
            raise RuntimeError(f"Failed to convert audio format: {e}")
    
    def add_effects(
        self,
        input_path: str,
        reverb: bool = False,
        echo: bool = False,
        output_path: Optional[str] = None
    ) -> str:
        """
        Add audio effects using ffmpeg
        
        Args:
            input_path: Path to input audio
            reverb: Apply reverb effect
            echo: Apply echo effect
            output_path: Path to output audio
            
        Returns:
            Path to processed audio
        """
        try:
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"effects_{timestamp}.wav")
            
            filters = []
            
            if echo:
                # Add echo effect
                filters.append("aecho=0.8:0.88:60:0.4")
            
            if reverb:
                # Add reverb effect (using equalizer as simple reverb)
                filters.append("equalizer=f=100:t=q:w=1:g=-3")
            
            if not filters:
                logger.warning("No effects specified, copying original")
                import shutil
                shutil.copy(input_path, output_path)
                return output_path
            
            logger.info(f"Adding effects: {', '.join(['echo' if echo else '', 'reverb' if reverb else ''])}")
            
            cmd = [
                "ffmpeg", "-i", input_path,
                "-af", ",".join(filters),
                "-ar", "44100",
                "-y",
                output_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            logger.info(f"Effects applied successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Effect processing failed: {e}")
            logger.warning("Returning original audio")
            return input_path
    
    def get_audio_duration(self, audio_path: str) -> float:
        """
        Get audio duration in seconds
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds
        """
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path
            ]
            
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            
            duration = float(result.stdout.strip())
            return duration
            
        except Exception as e:
            logger.error(f"Failed to get audio duration: {e}")
            return 0.0
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """
        Clean up old audio files
        
        Args:
            max_age_hours: Maximum file age in hours
        """
        import time
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        deleted_count = 0
        
        for audio_file in self.output_dir.glob("*.wav"):
            file_age = current_time - audio_file.stat().st_mtime
            
            if file_age > max_age_seconds:
                try:
                    audio_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old file: {audio_file.name}")
                except Exception as e:
                    logger.error(f"Failed to delete {audio_file.name}: {e}")
        
        logger.info(f"Cleanup complete. Deleted {deleted_count} files.")


# Singleton instance
_audio_processor = None

def get_audio_processor() -> AudioProcessor:
    """Get or create AudioProcessor singleton"""
    global _audio_processor
    if _audio_processor is None:
        _audio_processor = AudioProcessor()
    return _audio_processor

