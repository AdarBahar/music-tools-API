#!/bin/bash

# Music Tools API - Stem Separation Examples
# This script demonstrates different Demucs models and their use cases

BASE_URL="http://localhost:8001"
AUDIO_FILE="$1"

echo "🎛️ Music Tools API - Stem Separation Examples"
echo "=============================================="
echo ""

# Check if audio file is provided
if [ -z "$AUDIO_FILE" ]; then
    echo "❌ Please provide an audio file as the first argument"
    echo "Usage: $0 /path/to/your/audio.mp3"
    echo ""
    echo "Supported formats: MP3, WAV, FLAC, M4A, AAC, OPUS"
    exit 1
fi

# Check if file exists
if [ ! -f "$AUDIO_FILE" ]; then
    echo "❌ Audio file not found: $AUDIO_FILE"
    exit 1
fi

echo "🎵 Audio file: $AUDIO_FILE"
echo ""

# Function to test stem separation
test_separation() {
    local model=$1
    local description=$2
    local use_case=$3
    local output_format=$4
    local stems=$5
    
    echo "🤖 Testing Model: $model"
    echo "   Description: $description"
    echo "   Use case: $use_case"
    echo "   Output format: $output_format"
    echo "   Stems: $stems"
    echo ""
    echo "   Request:"
    
    local form_data="-F \"file=@$AUDIO_FILE\" -F \"model=$model\" -F \"output_format=$output_format\""
    if [ -n "$stems" ]; then
        form_data="$form_data -F \"stems=$stems\""
    fi
    
    echo "   curl -X POST \"$BASE_URL/api/v1/separate-stems\" $form_data"
    echo ""
    echo "   Response:"
    
    local cmd="curl -s -X POST \"$BASE_URL/api/v1/separate-stems\" -F \"file=@$AUDIO_FILE\" -F \"model=$model\" -F \"output_format=$output_format\""
    if [ -n "$stems" ]; then
        cmd="$cmd -F \"stems=$stems\""
    fi
    
    local response=$(eval $cmd)
    echo "$response" | jq -r '
        if .success then
            "   ✅ Success: Job ID " + .job_id + " (Processing time: " + (.processing_time_seconds | tostring) + "s)"
        else
            "   ❌ Error: " + (.error // "Unknown error")
        end'
    
    echo ""
    echo "   ---"
    echo ""
}

# Get available models first
echo "📋 Available Models:"
curl -s "$BASE_URL/api/v1/models" | jq -r '.models[] | "   • " + .name + ": " + .description'
echo ""

echo "📋 Available Formats:"
curl -s "$BASE_URL/api/v1/formats" | jq -r '.formats[] | "   • " + .format + ": " + .description'
echo ""
echo "🧪 Running Separation Tests..."
echo ""

# Test 1: Default model - Best overall quality
test_separation "htdemucs" "Hybrid Transformer Demucs - Best overall quality" "General music, rock, pop" "mp3" ""

# Test 2: Fine-tuned model - Best for vocals
test_separation "htdemucs_ft" "Fine-tuned Hybrid Transformer - Improved vocals" "Vocal-heavy tracks, karaoke" "wav" "vocals"

# Test 3: Electronic music optimized
test_separation "mdx_extra" "MDX Extra - Good for electronic music" "EDM, electronic, synthesized music" "flac" "vocals,drums,bass,other"

# Test 4: Fast processing
test_separation "mdx_extra_q" "MDX Extra Quantized - Faster processing" "Quick separation, preview quality" "mp3" "vocals,other"

echo ""
echo "📊 Model Comparison Summary:"
echo ""
echo "| Model        | Quality | Speed | Best For                    |"
echo "|--------------|---------|-------|-----------------------------|"
echo "| htdemucs     | ⭐⭐⭐⭐⭐ | ⭐⭐⭐   | General music (recommended) |"
echo "| htdemucs_ft  | ⭐⭐⭐⭐⭐ | ⭐⭐⭐   | Vocal separation            |"
echo "| mdx_extra    | ⭐⭐⭐⭐  | ⭐⭐⭐   | Electronic/EDM music        |"
echo "| mdx_extra_q  | ⭐⭐⭐    | ⭐⭐⭐⭐⭐ | Fast processing             |"
echo ""
echo "💡 Tips:"
echo "   • Use htdemucs for most music types (rock, pop, classical)"
echo "   • Use htdemucs_ft when vocals are the primary focus"
echo "   • Use mdx_extra for electronic music with heavy synthesis"
echo "   • Use mdx_extra_q when speed is more important than quality"
echo "   • Extract only needed stems (e.g., just vocals) for faster processing"
echo "   • WAV format provides highest quality, MP3 for smaller files"
echo ""
echo "🎯 Output Format Guide:"
echo "   • WAV: Uncompressed, highest quality, large files"
echo "   • FLAC: Lossless compression, good quality, medium files"
echo "   • MP3: Lossy compression, good quality, small files"
echo ""
echo "⏱️ Processing Times (approximate for 4-minute song):"
echo "   • htdemucs: 3-6 minutes"
echo "   • htdemucs_ft: 3-6 minutes"
echo "   • mdx_extra: 2-5 minutes"
echo "   • mdx_extra_q: 1-3 minutes"
echo "   • GPU acceleration: 3-5x faster"
echo ""
echo "📖 For complete documentation, visit: $BASE_URL/docs"
