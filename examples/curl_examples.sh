#!/bin/bash

# Music Tools API - cURL Examples
# Make sure the API server is running on localhost:8000

BASE_URL="http://localhost:8001"

echo "=== Music Tools API - cURL Examples ==="
echo

# Health Check
echo "1. Health Check"
curl -X GET "$BASE_URL/health" | jq
echo
echo

# Get Available Models
echo "2. Get Available Demucs Models"
curl -X GET "$BASE_URL/api/v1/models" | jq
echo
echo

# Get Supported Formats
echo "3. Get Supported Output Formats"
curl -X GET "$BASE_URL/api/v1/formats" | jq
echo
echo

# Get YouTube Video Info (without downloading)
echo "4. Get YouTube Video Information"
curl -X GET "$BASE_URL/api/v1/youtube-info?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ" | jq
echo
echo

# YouTube to MP3 Conversion - Best Quality
echo "5. Convert YouTube Video to MP3 (Best Quality)"
echo "   Note: Files are named using the video title (e.g., 'Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster).mp3')"
curl -X POST "$BASE_URL/api/v1/youtube-to-mp3" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "audio_quality": 0,
    "audio_format": "mp3",
    "extract_metadata": true
  }' | jq
echo
echo

# YouTube to MP3 Conversion - Balanced Quality
echo "6. Convert YouTube Video to MP3 (Balanced Quality)"
curl -X POST "$BASE_URL/api/v1/youtube-to-mp3" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "audio_quality": 5,
    "audio_format": "mp3",
    "extract_metadata": true
  }' | jq
echo
echo

# YouTube to MP3 Conversion - Small File Size
echo "7. Convert YouTube Video to MP3 (Small File Size)"
curl -X POST "$BASE_URL/api/v1/youtube-to-mp3" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "audio_quality": 8,
    "audio_format": "mp3",
    "extract_metadata": true
  }' | jq
echo
echo

# Get Available Models
echo "8. Get Available Demucs Models"
curl -X GET "$BASE_URL/api/v1/models" | jq
echo
echo

# Get Supported Formats
echo "9. Get Supported Output Formats"
curl -X GET "$BASE_URL/api/v1/formats" | jq
echo
echo

# Stem Separation Examples (requires audio file)
echo "10. Stem Separation Examples (requires audio file)"
echo "# Replace 'path/to/your/audio.mp3' with actual file path"
echo "# Note: Stems are named with original filename + stem type (e.g., 'Song Title - vocals.mp3')"
echo ""

echo "# Basic separation (all stems by default - no stems parameter needed)"
echo "curl -X POST \"$BASE_URL/api/v1/separate-stems\" \\"
echo "  -F \"file=@path/to/your/audio.mp3\" \\"
echo "  -F \"model=htdemucs\" \\"
echo "  -F \"output_format=mp3\" | jq"
echo "# Note: Omitting 'stems' parameter defaults to all stems (vocals,drums,bass,other)"
echo ""

echo "# Vocal separation only (faster)"
echo "curl -X POST \"$BASE_URL/api/v1/separate-stems\" \\"
echo "  -F \"file=@path/to/your/audio.mp3\" \\"
echo "  -F \"model=htdemucs_ft\" \\"
echo "  -F \"output_format=wav\" \\"
echo "  -F \"stems=vocals\" | jq"
echo ""

echo "# Electronic music optimized"
echo "curl -X POST \"$BASE_URL/api/v1/separate-stems\" \\"
echo "  -F \"file=@path/to/your/edm-track.mp3\" \\"
echo "  -F \"model=mdx_extra\" \\"
echo "  -F \"output_format=flac\" \\"
echo "  -F \"stems=vocals,drums,bass,other\" | jq"
echo ""

echo "# Fast processing (lower quality)"
echo "curl -X POST \"$BASE_URL/api/v1/separate-stems\" \\"
echo "  -F \"file=@path/to/your/audio.mp3\" \\"
echo "  -F \"model=mdx_extra_q\" \\"
echo "  -F \"output_format=mp3\" \\"
echo "  -F \"stems=vocals,other\" | jq"
echo
echo

# Download File (requires file_id from previous requests)
echo "7. Download Converted File"
echo "# Replace 'FILE_ID' with actual file ID from conversion"
echo "curl -X GET \"$BASE_URL/api/v1/download/FILE_ID\" -o downloaded_audio.mp3"
echo
echo

# Download Stem File (requires job_id from stem separation)
echo "8. Download Specific Stem"
echo "# Replace 'JOB_ID' with actual job ID from stem separation"
echo "# Note: Use the full filename from the API response (e.g., 'Song Title - vocals.mp3')"
echo "curl -X GET \"$BASE_URL/api/v1/download/JOB_ID/Song%20Title%20-%20vocals.mp3\" -o \"Song Title - vocals.mp3\""
echo
echo

# Get File Information
echo "9. Get File Information"
echo "# Replace 'FILE_ID' with actual file ID"
echo "curl -X GET \"$BASE_URL/api/v1/download/FILE_ID/info\" | jq"
echo
echo

# Storage Statistics
echo "10. Get Storage Statistics"
curl -X GET "$BASE_URL/api/v1/stats" | jq
echo
echo

# Manual Cleanup
echo "11. Trigger Manual Cleanup"
curl -X POST "$BASE_URL/api/v1/cleanup" | jq
echo
echo

echo "=== Examples Complete ==="
echo
echo "Notes:"
echo "- Make sure jq is installed for JSON formatting"
echo "- Replace placeholder values (FILE_ID, JOB_ID, file paths) with actual values"
echo "- YouTube downloads and stem separation may take several minutes"
echo "- Check the API documentation at $BASE_URL/docs for more details"
