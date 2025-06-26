#!/bin/bash

# Music Tools API - Audio Quality Examples
# This script demonstrates different audio quality settings

BASE_URL="http://localhost:8001"
YOUTUBE_URL="https://www.youtube.com/watch?v=dQw4w9WgXcQ"

echo "🎵 Music Tools API - Audio Quality Examples"
echo "==========================================="
echo ""
echo "Testing different audio quality settings with the same video:"
echo "URL: $YOUTUBE_URL"
echo ""

# Function to test audio quality
test_quality() {
    local quality=$1
    local description=$2
    local use_case=$3
    
    echo "📊 Testing Quality $quality - $description"
    echo "   Use case: $use_case"
    echo "   Request:"
    
    local payload='{
        "url": "'$YOUTUBE_URL'",
        "audio_quality": '$quality',
        "audio_format": "mp3",
        "extract_metadata": true
    }'
    
    echo "   $payload"
    echo ""
    echo "   Response:"
    
    curl -s -X POST "$BASE_URL/api/v1/youtube-to-mp3" \
        -H "Content-Type: application/json" \
        -d "$payload" | jq -r '
        if .success then
            "   ✅ Success: " + .filename + " (" + (.file_size_mb | tostring) + " MB)"
        else
            "   ❌ Error: " + .error
        end'
    
    echo ""
    echo "   ---"
    echo ""
}

# Test different quality levels
echo "🔊 BEST QUALITY (Archival/Audiophile)"
test_quality 0 "Best Quality" "Archival, audiophiles, studio work"

echo "🔊 HIGH QUALITY"
test_quality 2 "Very High Quality" "Premium listening, high-end headphones"

echo "🔊 BALANCED QUALITY (Recommended)"
test_quality 5 "Default Quality" "General use, good balance of quality and size"

echo "🔊 MOBILE/STREAMING QUALITY"
test_quality 7 "Lower Quality" "Mobile devices, streaming, limited bandwidth"

echo "🔊 SMALLEST FILES"
test_quality 10 "Worst Quality" "Voice content, podcasts, very limited storage"

echo ""
echo "📋 Quality Comparison Summary:"
echo ""
echo "| Quality | Bitrate   | 4min Song | Use Case                    |"
echo "|---------|-----------|-----------|----------------------------|"
echo "| 0       | ~320 kbps | ~9-10 MB  | Archival, audiophiles      |"
echo "| 2       | ~256 kbps | ~7-8 MB   | Premium quality            |"
echo "| 5       | ~160 kbps | ~4-5 MB   | General use (recommended)  |"
echo "| 7       | ~112 kbps | ~3 MB     | Mobile, streaming          |"
echo "| 10      | ~64 kbps  | ~2 MB     | Voice, podcasts            |"
echo ""
echo "💡 Tips:"
echo "   • Use quality 0-2 for music you want to keep long-term"
echo "   • Use quality 5 for everyday listening (good balance)"
echo "   • Use quality 7-10 for temporary downloads or limited storage"
echo "   • Higher quality = larger files but better audio"
echo "   • Lower quality = smaller files but reduced audio fidelity"
echo ""
echo "🎯 Format Recommendations:"
echo "   • MP3: Universal compatibility"
echo "   • M4A: Better quality than MP3 at same bitrate"
echo "   • FLAC: Lossless quality (much larger files)"
echo "   • AAC: Good for mobile devices"
echo ""
echo "📖 For complete documentation, visit: $BASE_URL/docs"
