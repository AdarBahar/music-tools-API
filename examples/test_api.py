"""
Example script to test the Music Tools API
"""

import requests
import json
import time
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8001"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_youtube_info():
    """Test YouTube info extraction"""
    print("Testing YouTube info extraction...")
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll
    response = requests.get(f"{BASE_URL}/api/v1/youtube-info", params={"url": url})
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Title: {data['info']['title']}")
        print(f"Duration: {data['info']['duration']} seconds")
        print(f"Uploader: {data['info']['uploader']}")
    else:
        print(f"Error: {response.text}")
    print()

def test_youtube_to_mp3():
    """Test YouTube to MP3 conversion"""
    print("Testing YouTube to MP3 conversion...")
    
    payload = {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "audio_quality": 0,
        "audio_format": "mp3",
        "extract_metadata": True
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/youtube-to-mp3", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['success']}")
        print(f"File ID: {data['file_id']}")
        print(f"Filename: {data['filename']}")
        print(f"File Size: {data['file_size_mb']} MB")
        print(f"Download URL: {data['download_url']}")
        
        if data['metadata']:
            print(f"Title: {data['metadata']['title']}")
            print(f"Duration: {data['metadata']['duration']} seconds")
        
        return data['file_id']
    else:
        print(f"Error: {response.text}")
        return None
    print()

def test_stem_separation(audio_file_path=None):
    """Test stem separation"""
    print("Testing stem separation...")
    
    if not audio_file_path:
        print("No audio file provided for stem separation test")
        return None
    
    if not Path(audio_file_path).exists():
        print(f"Audio file not found: {audio_file_path}")
        return None
    
    # Prepare the file upload
    with open(audio_file_path, 'rb') as f:
        files = {'file': (Path(audio_file_path).name, f, 'audio/mpeg')}
        data = {
            'model': 'htdemucs',
            'output_format': 'mp3',
            'stems': 'vocals,drums,bass,other'
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/separate-stems", files=files, data=data)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['success']}")
        print(f"Job ID: {data['job_id']}")
        print(f"Processing Time: {data['processing_time_seconds']} seconds")
        
        if data['stems']:
            print("Stem URLs:")
            for stem_name, url in data['stems'].items():
                if url:
                    print(f"  {stem_name}: {url}")
        
        return data['job_id']
    else:
        print(f"Error: {response.text}")
        return None
    print()

def test_download_file(file_id):
    """Test file download"""
    if not file_id:
        print("No file ID provided for download test")
        return
    
    print(f"Testing file download for ID: {file_id}")
    response = requests.get(f"{BASE_URL}/api/v1/download/{file_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Content-Length: {response.headers.get('content-length')} bytes")
        print("Download successful!")
    else:
        print(f"Error: {response.text}")
    print()

def test_get_models():
    """Test getting available models"""
    print("Testing available models...")
    response = requests.get(f"{BASE_URL}/api/v1/models")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Default model: {data['default_model']}")
        print("Available models:")
        for model in data['models']:
            print(f"  {model['name']}: {model['description']}")
    else:
        print(f"Error: {response.text}")
    print()

def test_get_formats():
    """Test getting supported formats"""
    print("Testing supported formats...")
    response = requests.get(f"{BASE_URL}/api/v1/formats")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Default format: {data['default_format']}")
        print("Available formats:")
        for format_info in data['formats']:
            print(f"  {format_info['format']}: {format_info['description']}")
    else:
        print(f"Error: {response.text}")
    print()

def test_storage_stats():
    """Test storage statistics"""
    print("Testing storage statistics...")
    response = requests.get(f"{BASE_URL}/api/v1/stats")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total files: {data['total_files']}")
        print(f"Total size: {data['total_size_mb']} MB")
        print("Directory stats:")
        for dir_name, stats in data['directories'].items():
            if isinstance(stats, dict) and 'file_count' in stats:
                print(f"  {dir_name}: {stats['file_count']} files, {stats['total_size_mb']} MB")
    else:
        print(f"Error: {response.text}")
    print()

def main():
    """Run all tests"""
    print("=== Music Tools API Test Suite ===\n")
    
    # Basic tests
    test_health_check()
    test_get_models()
    test_get_formats()
    test_storage_stats()
    
    # YouTube tests
    test_youtube_info()
    
    # Uncomment to test actual downloads (takes time)
    # file_id = test_youtube_to_mp3()
    # if file_id:
    #     test_download_file(file_id)
    
    # Stem separation test (requires audio file)
    # Uncomment and provide path to test stem separation
    # job_id = test_stem_separation("path/to/your/audio.mp3")
    
    print("=== Test Suite Complete ===")

if __name__ == "__main__":
    main()
