"""
Audio stem separation service using Demucs
"""

import os
import uuid
import time
import logging
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.core.config import settings
from app.core.memory_management import (
    memory_monitor, operation_limiter, process_manager, efficient_processor
)

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when security validation fails"""
    pass


class StemSeparationService:
    """Service for separating audio into stems using Demucs"""
    
    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR
        self.temp_dir = settings.TEMP_DIR
    
    def _validate_model_name(self, model: str) -> str:
        """
        Validate model name against whitelist to prevent injection
        
        Args:
            model: Model name to validate
            
        Returns:
            Validated model name
            
        Raises:
            SecurityError: If model name is invalid
        """
        if not model or not isinstance(model, str):
            raise SecurityError("Model name must be a non-empty string")
        
        # Remove any potentially dangerous characters
        cleaned_model = ''.join(c for c in model if c.isalnum() or c in '-_.')
        
        # Validate against whitelist
        supported_models = settings.supported_demucs_models_list
        if cleaned_model not in supported_models:
            logger.error(f"Security validation failed: Invalid model '{cleaned_model}'. Supported models: {supported_models}")
            raise SecurityError(f"Invalid model '{cleaned_model}'. Supported models: {supported_models}")
        
        logger.debug(f"Model validation passed: {cleaned_model}")
        return cleaned_model
    
    def _validate_file_path(self, file_path: str, must_exist: bool = True) -> Path:
        """
        Validate and sanitize file paths to prevent path traversal
        
        Args:
            file_path: File path to validate
            must_exist: Whether the file must exist
            
        Returns:
            Validated Path object
            
        Raises:
            SecurityError: If path is invalid or unsafe
        """
        if not file_path or not isinstance(file_path, str):
            raise SecurityError("File path must be a non-empty string")
        
        try:
            # Convert to Path and resolve to absolute path
            path = Path(file_path).resolve()
            
            # Ensure path doesn't contain dangerous sequences
            path_str = str(path)
            
            # Define allowed directories (temporary directories and uploads)
            base_dir = str(settings.BASE_DIR.resolve())
            temp_dir = str(settings.TEMP_DIR.resolve())
            output_dir = str(settings.OUTPUT_DIR.resolve())
            upload_dir = str(settings.UPLOAD_DIR.resolve())
            allowed_prefixes = [
                '/tmp/',
                '/var/folders/',  # macOS temp directories
                '/private/var/folders/',  # macOS temp directories (resolved)
                '/private/tmp/',  # macOS temp directories (resolved)
                str(Path.cwd()),  # Current working directory
                tempfile.gettempdir(),  # System temp directory
                base_dir,
                temp_dir,
                output_dir,
                upload_dir,
            ]
            
            # Check if path is in allowed directories
            path_allowed = any(path_str.startswith(prefix) for prefix in allowed_prefixes)
            if not path_allowed:
                raise SecurityError(f"File path not in allowed directories: {path_str}")
            
            # Additional security checks
            dangerous_sequences = ['..', ';', '&&', '||', '|', '`', '$', '>', '<']
            if any(seq in path_str for seq in dangerous_sequences):
                raise SecurityError(f"Potentially unsafe file path: {path_str}")
            
            # Check if file exists when required
            if must_exist and not path.exists():
                raise SecurityError(f"File does not exist: {path_str}")
            
            # Ensure it's a file (not directory) when it exists
            if path.exists() and not path.is_file():
                raise SecurityError(f"Path is not a regular file: {path_str}")
            
            logger.debug(f"File path validation passed: {path_str}")
            return path
            
        except (OSError, ValueError) as e:
            raise SecurityError(f"Invalid file path '{file_path}': {e}")
    
    def _validate_output_format(self, format_name: str) -> str:
        """
        Validate output format against whitelist
        
        Args:
            format_name: Format to validate
            
        Returns:
            Validated format name
            
        Raises:
            SecurityError: If format is invalid
        """
        if not format_name or not isinstance(format_name, str):
            raise SecurityError("Format must be a non-empty string")
        
        # Clean and validate format
        cleaned_format = format_name.lower().strip()
        if cleaned_format not in settings.SUPPORTED_STEM_FORMATS:
            raise SecurityError(f"Invalid format '{cleaned_format}'. Supported: {settings.SUPPORTED_STEM_FORMATS}")
        
        return cleaned_format

    def _ensure_disk_space(self, path: Path, required_bytes: int, label: str) -> None:
        """Ensure filesystem containing `path` has `required_bytes` free."""
        try:
            usage = shutil.disk_usage(str(path))
            if usage.free < required_bytes:
                free_mb = usage.free / (1024 * 1024)
                req_mb = required_bytes / (1024 * 1024)
                raise SecurityError(
                    f"Insufficient disk space in {label} ({path}). "
                    f"Free: {free_mb:.0f}MB, required (estimate): {req_mb:.0f}MB. "
                    f"Clean up /var/www/apitools/temp and /var/www/apitools/outputs or move TEMP_DIR/OUTPUT_DIR to a larger disk."
                )
        except FileNotFoundError:
            # If the directory doesn't exist yet, let upstream create it.
            return
        except SecurityError:
            raise
        except Exception as e:
            logger.warning(f"Disk space check failed for {label} at {path}: {type(e).__name__}")

    def _estimate_required_temp_bytes(self, audio_path: Path, stem_count: int) -> Optional[int]:
        """Estimate temp bytes needed for Demucs WAV stems.

        Uses ffprobe to get duration quickly without decoding full audio.
        Returns None if duration can't be determined.
        """
        try:
            # ffprobe returns duration in seconds (float)
            probe = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(audio_path),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if probe.returncode != 0:
                return None
            duration_s = float((probe.stdout or "").strip())
            if duration_s <= 0:
                return None

            # Conservative estimate: float32 WAV, stereo, 44.1kHz
            sample_rate = 44100
            channels = 2
            bytes_per_sample = 4
            bytes_per_second_per_stem = sample_rate * channels * bytes_per_sample

            # Add headroom: demucs writes multiple files and there is container overhead.
            safety_factor = 2.0
            base = duration_s * bytes_per_second_per_stem * max(1, stem_count)
            return int(base * safety_factor)
        except (ValueError, TimeoutError):
            return None
        except FileNotFoundError:
            # ffprobe not installed
            return None
        except Exception:
            return None
    
    async def separate_stems(
        self,
        audio_file_path: str,
        model: str = "htdemucs",
        output_format: str = "mp3",
        stems: Optional[List[str]] = None,
        original_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Separate audio file into stems with memory management

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
            # Security validation - CRITICAL for preventing command injection
            validated_model = self._validate_model_name(model)
            validated_audio_path = self._validate_file_path(audio_file_path, must_exist=True)
            validated_format = self._validate_output_format(output_format)
            
            # Validate stems if provided
            validated_stems = None
            if stems:
                valid_stem_names = ['vocals', 'drums', 'bass', 'other']
                validated_stems = []
                for stem in stems:
                    if not isinstance(stem, str) or stem not in valid_stem_names:
                        raise SecurityError(f"Invalid stem name '{stem}'. Valid: {valid_stem_names}")
                    validated_stems.append(stem)
            
            # Memory management: estimate required memory and check availability
            file_size = validated_audio_path.stat().st_size
            estimated_memory = efficient_processor.estimate_processing_memory(file_size, 'stem_separation')
            
            logger.info(f"Starting stem separation: model={validated_model}, format={validated_format}, stems={validated_stems}")
            logger.info(f"File size: {file_size / 1024 / 1024:.1f}MB, estimated memory: {estimated_memory}MB")

            # Fail fast if we don't have enough disk space for Demucs WAV outputs.
            # Demucs writes WAV stems into TEMP_DIR before we convert/move them.
            required_temp_bytes = self._estimate_required_temp_bytes(validated_audio_path, stem_count=len(validated_stems) if validated_stems else 4)
            if required_temp_bytes is not None:
                self._ensure_disk_space(Path(self.temp_dir), required_temp_bytes, label="TEMP_DIR")
            # Also ensure some space in OUTPUT_DIR for final converted stems.
            self._ensure_disk_space(Path(self.output_dir), 256 * 1024 * 1024, label="OUTPUT_DIR")
            
            # Acquire operation slot with memory check
            async with operation_limiter.acquire_operation_slot(f"stem_separation_{job_id}", estimated_memory):
            
                # Create temporary directory for processing
                with tempfile.TemporaryDirectory(dir=self.temp_dir) as temp_process_dir:
                    
                    # Run Demucs separation with validated inputs
                    demucs_output_dir = os.path.join(temp_process_dir, "demucs_output")
                    
                    # Build command with validated parameters - NO USER INPUT DIRECTLY PASSED
                    cmd = [
                        "python", "-m", "demucs.separate",
                        "-n", validated_model,  # Validated against whitelist
                        "-o", demucs_output_dir,  # Our controlled directory
                        str(validated_audio_path)  # Validated file path
                    ]
                    
                    logger.info(f"Running Demucs with validated command: {' '.join(cmd[:6])}... (path hidden for security)")
                    
                    # Check memory before starting intensive operation
                    if not memory_monitor.check_memory_available(estimated_memory):
                        return {
                            'success': False,
                            'error': f"Insufficient memory for processing. Required: {estimated_memory}MB"
                        }
                    
                    # Run Demucs with process monitoring
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    # Monitor process memory usage
                    process_manager.monitor_process(process, f"demucs_{job_id}")
                    
                    # Wait for completion with configurable timeout
                    timeout_seconds = settings.STEM_SEPARATION_TIMEOUT
                    try:
                        stdout, stderr = process.communicate(timeout=timeout_seconds)
                        result_returncode = process.returncode
                    except subprocess.TimeoutExpired:
                        process.terminate()
                        process.wait()
                        raise subprocess.TimeoutExpired(cmd, timeout_seconds)
                
                    if result_returncode != 0:
                        logger.error(f"Demucs failed: {stderr}")
                        return {
                            'success': False,
                            'error': f"Demucs separation failed: {stderr}"
                        }
                    
                    # Check memory usage after processing
                    if memory_monitor.check_memory_warning():
                        logger.warning("Memory usage high after Demucs processing")
                    
                    # Find the separated stems
                    stems_dir = self._find_stems_directory(demucs_output_dir)
                    if not stems_dir:
                        return {
                            'success': False,
                            'error': "Could not find separated stems in output"
                        }
                    
                    # Convert and move stems to final location with validated parameters
                    stem_files = await self._process_stems(
                        stems_dir, job_id, validated_format, validated_stems, original_filename
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
        except SecurityError:
            # Re-raise security errors so API layer can handle them appropriately
            raise
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
    
    async def _process_stems(
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
                        # Use memory-efficient copying for WAV files
                        await efficient_processor.copy_file_chunked(
                            Path(input_file), output_file
                        )
                    else:
                        # Convert using ffmpeg
                        success = await self._convert_audio_format_async(input_file, str(output_file), output_format)
                        if not success:
                            logger.warning(f"Failed to convert {stem_name} to {output_format}")
                            continue
                    
                    stem_files[stem_name] = str(output_file)
                    logger.info(f"Processed stem: {stem_name} -> {output_filename}")
            
            return stem_files
            
        except Exception as e:
            logger.error(f"Error processing stems: {e}")
            return {}
    
    async def _convert_audio_format_async(self, input_file: str, output_file: str, format: str) -> bool:
        """
        Convert audio file to specified format using ffmpeg with memory management
        
        Args:
            input_file: Input file path
            output_file: Output file path  
            format: Target format
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            # Security validation - CRITICAL for preventing command injection
            validated_input = self._validate_file_path(input_file, must_exist=True)
            validated_output = self._validate_file_path(output_file, must_exist=False)
            validated_format = self._validate_output_format(format)
            
            # Ensure output directory exists
            validated_output.parent.mkdir(parents=True, exist_ok=True)
            
            # Check memory before conversion
            file_size = validated_input.stat().st_size
            estimated_memory = efficient_processor.estimate_processing_memory(file_size, 'format_conversion')
            
            if not memory_monitor.check_memory_available(estimated_memory):
                logger.error(f"Insufficient memory for audio conversion: requires {estimated_memory}MB")
                return False
            
            # Build command with validated parameters only
            cmd = ["ffmpeg", "-i", str(validated_input), "-y"]  # -y to overwrite
            
            # Add format-specific options (whitelist approach)
            if validated_format == "mp3":
                cmd.extend(["-codec:a", "libmp3lame", "-b:a", "192k"])
            elif validated_format == "flac":
                cmd.extend(["-codec:a", "flac"])
            elif validated_format == "m4a":
                cmd.extend(["-codec:a", "aac", "-b:a", "192k"])
            else:
                # This should never happen due to validation, but be safe
                logger.error(f"Unsupported format after validation: {validated_format}")
                return False
            
            cmd.append(str(validated_output))
            
            logger.debug(f"Running FFmpeg conversion: {validated_format} (paths hidden for security)")
            
            # Run async to avoid blocking
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            
            def _run_ffmpeg():
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Monitor process memory
                process_manager.monitor_process(process, f"ffmpeg_conversion")
                
                try:
                    stdout, stderr = process.communicate(timeout=300)  # 5 minute timeout
                    return process.returncode, stderr
                except subprocess.TimeoutExpired:
                    process.terminate()
                    process.wait()
                    return 1, "Conversion timed out"
            
            # Run in thread pool
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                returncode, stderr = await loop.run_in_executor(executor, _run_ffmpeg)
            
            if returncode != 0:
                logger.error(f"FFmpeg conversion failed for {validated_format}: {stderr}")
                return False
            
            return True
        
        except SecurityError as e:
            logger.error(f"Security validation failed in FFmpeg conversion: {e}")
            return False
        except Exception as e:
            logger.error(f"Error converting audio: {e}")
            return False

    def _convert_audio_format(self, input_file: str, output_file: str, format: str) -> bool:
        """
        Convert audio file to specified format using ffmpeg with security validation
        
        Args:
            input_file: Input file path
            output_file: Output file path  
            format: Target format
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            # Security validation - CRITICAL for preventing command injection
            validated_input = self._validate_file_path(input_file, must_exist=True)
            validated_output = self._validate_file_path(output_file, must_exist=False)
            validated_format = self._validate_output_format(format)
            
            # Ensure output directory exists
            validated_output.parent.mkdir(parents=True, exist_ok=True)
            
            # Build command with validated parameters only
            cmd = ["ffmpeg", "-i", str(validated_input), "-y"]  # -y to overwrite
            
            # Add format-specific options (whitelist approach)
            if validated_format == "mp3":
                cmd.extend(["-codec:a", "libmp3lame", "-b:a", "192k"])
            elif validated_format == "flac":
                cmd.extend(["-codec:a", "flac"])
            elif validated_format == "m4a":
                cmd.extend(["-codec:a", "aac", "-b:a", "192k"])
            else:
                # This should never happen due to validation, but be safe
                logger.error(f"Unsupported format after validation: {validated_format}")
                return False
            
            cmd.append(str(validated_output))
            
            logger.debug(f"Running FFmpeg conversion: {validated_format} (paths hidden for security)")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for conversion
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg conversion failed for {validated_format}: {result.stderr}")
                return False
            
            return True
        
        except SecurityError as e:
            logger.error(f"Security validation failed in FFmpeg conversion: {e}")
            return False
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
