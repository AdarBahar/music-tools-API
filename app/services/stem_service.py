"""
Audio stem separation service using Demucs
"""

import os
import uuid
import time
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class StemSeparationService:
    """Service for separating audio into stems using Demucs"""
    
    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR
        self.temp_dir = settings.TEMP_DIR
    
    def separate_stems(
        self,
        audio_file_path: str,
        model: str = "htdemucs",
        output_format: str = "mp3",
        stems: Optional[List[str]] = None,
        original_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Separate audio file into stems

        Args:
            audio_file_path: Path to the input audio file
            model: Demucs model to use
            output_format: Output format for stems
            stems: Specific stems to extract (None for all)
            original_filename: Original filename to use for naming stems (without extension)

        Returns:
            Dictionary with separation results
        """
        job_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Create temporary directory for processing
            with tempfile.TemporaryDirectory(dir=self.temp_dir) as temp_process_dir:
                
                # Run Demucs separation
                demucs_output_dir = os.path.join(temp_process_dir, "demucs_output")
                
                cmd = [
                    "python", "-m", "demucs.separate",
                    "-n", model,
                    "-o", demucs_output_dir,
                    audio_file_path
                ]
                
                logger.info(f"Running Demucs with command: {' '.join(cmd)}")
                
                # Run Demucs
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30 minute timeout
                )
                
                if result.returncode != 0:
                    logger.error(f"Demucs failed: {result.stderr}")
                    return {
                        'success': False,
                        'error': f"Demucs separation failed: {result.stderr}"
                    }
                
                # Find the separated stems
                stems_dir = self._find_stems_directory(demucs_output_dir)
                if not stems_dir:
                    return {
                        'success': False,
                        'error': "Could not find separated stems in output"
                    }
                
                # Convert and move stems to final location
                stem_files = self._process_stems(
                    stems_dir, job_id, output_format, stems, original_filename
                )
                
                if not stem_files:
                    return {
                        'success': False,
                        'error': "No stem files were created"
                    }
                
                processing_time = time.time() - start_time
                
                return {
                    'success': True,
                    'job_id': job_id,
                    'stem_files': stem_files,
                    'processing_time_seconds': round(processing_time, 2)
                }
                
        except subprocess.TimeoutExpired:
            logger.error("Demucs processing timed out")
            return {
                'success': False,
                'error': "Processing timed out (maximum 30 minutes)"
            }
        except Exception as e:
            logger.error(f"Unexpected error during stem separation: {e}")
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            }
    
    def _find_stems_directory(self, demucs_output_dir: str) -> Optional[str]:
        """Find the directory containing separated stems"""
        try:
            # Demucs creates a nested directory structure
            # Look for the actual stems directory
            for root, dirs, files in os.walk(demucs_output_dir):
                # Look for directories containing .wav files
                wav_files = [f for f in files if f.endswith('.wav')]
                if len(wav_files) >= 2:  # Should have at least 2 stems
                    return root
            return None
        except Exception as e:
            logger.error(f"Error finding stems directory: {e}")
            return None
    
    def _process_stems(
        self,
        stems_dir: str,
        job_id: str,
        output_format: str,
        requested_stems: Optional[List[str]] = None,
        original_filename: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Process and convert stems to the requested format

        Args:
            stems_dir: Directory containing the separated stems
            job_id: Unique job identifier
            output_format: Target output format
            requested_stems: Specific stems to process (None for all)
            original_filename: Original filename to use for naming stems (without extension)

        Returns:
            Dictionary mapping stem names to file paths
        """
        stem_files = {}
        
        # Create job-specific output directory
        job_output_dir = self.output_dir / job_id
        job_output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Find all stem files
            available_stems = {}
            for filename in os.listdir(stems_dir):
                if filename.endswith('.wav'):
                    stem_name = filename.replace('.wav', '')
                    available_stems[stem_name] = os.path.join(stems_dir, filename)
            
            # Process requested stems (or all if none specified)
            stems_to_process = requested_stems if requested_stems else list(available_stems.keys())
            
            for stem_name in stems_to_process:
                if stem_name in available_stems:
                    input_file = available_stems[stem_name]

                    # Generate output filename based on original filename or fallback to stem name
                    if original_filename:
                        # Remove extension from original filename if present
                        base_name = original_filename
                        if '.' in base_name:
                            base_name = '.'.join(base_name.split('.')[:-1])
                        output_filename = f"{base_name} - {stem_name}.{output_format}"
                    else:
                        output_filename = f"{stem_name}.{output_format}"

                    output_file = job_output_dir / output_filename
                    
                    if output_format == "wav":
                        # Just copy the file if output format is wav
                        import shutil
                        shutil.copy2(input_file, output_file)
                    else:
                        # Convert using ffmpeg
                        success = self._convert_audio_format(input_file, str(output_file), output_format)
                        if not success:
                            logger.warning(f"Failed to convert {stem_name} to {output_format}")
                            continue
                    
                    stem_files[stem_name] = str(output_file)
                    logger.info(f"Processed stem: {stem_name} -> {output_filename}")
            
            return stem_files
            
        except Exception as e:
            logger.error(f"Error processing stems: {e}")
            return {}
    
    def _convert_audio_format(self, input_file: str, output_file: str, format: str) -> bool:
        """
        Convert audio file to specified format using ffmpeg
        
        Args:
            input_file: Input file path
            output_file: Output file path
            format: Target format
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            cmd = ["ffmpeg", "-i", input_file, "-y"]  # -y to overwrite
            
            # Add format-specific options
            if format == "mp3":
                cmd.extend(["-codec:a", "libmp3lame", "-b:a", "192k"])
            elif format == "flac":
                cmd.extend(["-codec:a", "flac"])
            elif format == "m4a":
                cmd.extend(["-codec:a", "aac", "-b:a", "192k"])
            
            cmd.append(output_file)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for conversion
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg conversion failed: {result.stderr}")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Audio conversion timed out")
            return False
        except Exception as e:
            logger.error(f"Error converting audio: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available Demucs models"""
        return settings.SUPPORTED_DEMUCS_MODELS
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats"""
        return settings.SUPPORTED_STEM_FORMATS
