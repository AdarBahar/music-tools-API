"""
Python client example for Music Tools API
"""

import requests
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any


class MusicToolsClient:
    """Python client for Music Tools API"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health status"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_youtube_info(self, url: str) -> Dict[str, Any]:
        """Get YouTube video information without downloading"""
        response = self.session.get(
            f"{self.base_url}/api/v1/youtube-info",
            params={"url": url}
        )
        response.raise_for_status()
        return response.json()
    
    def youtube_to_mp3(
        self,
        url: str,
        audio_quality: int = 0,
        audio_format: str = "mp3",
        extract_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Convert YouTube video to MP3

        Returns a dict with 'filename' using the video title
        (e.g., 'Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster).mp3')
        """
        payload = {
            "url": url,
            "audio_quality": audio_quality,
            "audio_format": audio_format,
            "extract_metadata": extract_metadata
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/youtube-to-mp3",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def separate_stems(
        self,
        audio_file_path: str,
        model: str = "htdemucs",
        output_format: str = "mp3",
        stems: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Separate audio file into stems using AI models

        Args:
            audio_file_path: Path to audio file
            model: Demucs model ('htdemucs', 'htdemucs_ft', 'mdx_extra', 'mdx_extra_q')
            output_format: Output format ('wav', 'mp3', 'flac')
            stems: Comma-separated stems ('vocals,drums,bass,other' or subset).
                   If None or empty, defaults to all stems.

        Returns:
            Dict with 'stems' containing URLs to download files named with original filename + stem type
            (e.g., 'Song Title - vocals.mp3', 'Song Title - drums.mp3')
        """
        if not Path(audio_file_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        with open(audio_file_path, 'rb') as f:
            files = {'file': (Path(audio_file_path).name, f, 'audio/mpeg')}
            data = {
                'model': model,
                'output_format': output_format
            }
            if stems:
                data['stems'] = stems

            response = self.session.post(
                f"{self.base_url}/api/v1/separate-stems",
                files=files,
                data=data
            )

        response.raise_for_status()
        return response.json()

    def get_available_models(self) -> Dict[str, Any]:
        """Get available Demucs models"""
        response = self.session.get(f"{self.base_url}/api/v1/models")
        response.raise_for_status()
        return response.json()

    def get_supported_formats(self) -> Dict[str, Any]:
        """Get supported output formats"""
        response = self.session.get(f"{self.base_url}/api/v1/formats")
        response.raise_for_status()
        return response.json()
    
    def download_file(self, file_id: str, output_path: str) -> bool:
        """Download a converted audio file"""
        response = self.session.get(f"{self.base_url}/api/v1/download/{file_id}")
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return True
    
    def download_stem(self, job_id: str, filename: str, output_path: str) -> bool:
        """
        Download a specific stem file

        Args:
            job_id: Job ID from stem separation
            filename: Full filename from API response (e.g., 'Song Title - vocals.mp3')
            output_path: Local path to save the file
        """
        response = self.session.get(f"{self.base_url}/api/v1/download/{job_id}/{filename}")
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return True
    
    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Get information about a file"""
        response = self.session.get(f"{self.base_url}/api/v1/download/{file_id}/info")
        response.raise_for_status()
        return response.json()
    
    def get_available_models(self) -> Dict[str, Any]:
        """Get available Demucs models"""
        response = self.session.get(f"{self.base_url}/api/v1/models")
        response.raise_for_status()
        return response.json()
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """Get supported output formats"""
        response = self.session.get(f"{self.base_url}/api/v1/formats")
        response.raise_for_status()
        return response.json()
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        response = self.session.get(f"{self.base_url}/api/v1/stats")
        response.raise_for_status()
        return response.json()
    
    def trigger_cleanup(self) -> Dict[str, Any]:
        """Trigger manual cleanup"""
        response = self.session.post(f"{self.base_url}/api/v1/cleanup")
        response.raise_for_status()
        return response.json()


def example_usage():
    """Example usage of the client"""
    client = MusicToolsClient()
    
    try:
        # Check API health
        print("Checking API health...")
        health = client.health_check()
        print(f"API Status: {health['status']}")
        
        # Get YouTube video info
        print("\nGetting YouTube video info...")
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        info = client.get_youtube_info(url)
        print(f"Video Title: {info['info']['title']}")
        print(f"Duration: {info['info']['duration']} seconds")
        
        # Convert to MP3 (uncomment to test)
        # print("\nConverting to MP3...")
        # result = client.youtube_to_mp3(url)
        # if result['success']:
        #     print(f"Conversion successful! File ID: {result['file_id']}")
        #     
        #     # Download the file
        #     print("Downloading file...")
        #     client.download_file(result['file_id'], "downloaded_audio.mp3")
        #     print("Download complete!")
        
        # Get available models
        print("\nAvailable Demucs models:")
        models = client.get_available_models()
        for model in models['models']:
            recommended = " (Recommended)" if model['recommended'] else ""
            print(f"  • {model['name']}: {model['description']}{recommended}")

        # Get supported formats
        print("\nSupported output formats:")
        formats = client.get_supported_formats()
        for fmt in formats['formats']:
            print(f"  • {fmt['format']}: {fmt['description']}")

        # Stem separation examples (commented out - provide audio file to test)
        print("\nStem separation examples (uncomment and provide audio file):")
        print("""
        # Example 1: General music separation (all stems - default behavior)
        # result = client.separate_stems(
        #     "path/to/your/audio.mp3",
        #     model="htdemucs",
        #     output_format="mp3"
        #     # Note: stems parameter omitted - defaults to all stems
        # )

        # Example 2: Vocal extraction only (faster)
        # result = client.separate_stems(
        #     "path/to/your/audio.mp3",
        #     model="htdemucs_ft",
        #     output_format="wav",
        #     stems="vocals"
        # )

        # Example 3: Electronic music optimized (all stems explicitly)
        # result = client.separate_stems(
        #     "path/to/your/edm-track.mp3",
        #     model="mdx_extra",
        #     output_format="flac",
        #     stems="vocals,drums,bass,other"  # Same as omitting stems parameter
        # )
        """)

        # Get storage stats
        print("\nStorage statistics:")
        stats = client.get_storage_stats()
        print(f"Total files: {stats['total_files']}")
        print(f"Total size: {stats['total_size_mb']} MB")
        
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    example_usage()
