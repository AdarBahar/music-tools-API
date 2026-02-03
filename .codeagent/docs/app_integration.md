# 🔌 Music Tools API Integration Guide

This guide provides detailed instructions for integrating the Music Tools API into your applications, with code examples in Node.js.

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Base Configuration](#base-configuration)
4. [API Endpoints](#api-endpoints)
   - [Health Check](#health-check)
   - [YouTube to MP3](#youtube-to-mp3)
   - [Stem Separation](#stem-separation)
   - [File Download](#file-download)
5. [Complete Integration Example](#complete-integration-example)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Best Practices](#best-practices)

---

## Overview

The Music Tools API provides two main services:

| Service | Description |
|---------|-------------|
| **YouTube to MP3** | Convert YouTube videos to audio files (MP3, WAV, FLAC, etc.) |
| **Stem Separation** | Separate audio files into individual stems (vocals, drums, bass, other) |

**Base URL:** `https://apitools.bahar.co.il`

---

## Authentication

All API endpoints require authentication via an API key passed in the `X-API-Key` header.

```javascript
const headers = {
  'X-API-Key': 'your-api-key-here',
  'Content-Type': 'application/json'
};
```

---

## Base Configuration

### Install Dependencies

```bash
npm install axios form-data fs
```

### Create API Client

```javascript
// musicToolsApi.js
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');

class MusicToolsAPI {
  constructor(apiKey, baseUrl = 'https://apitools.bahar.co.il') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    this.client = axios.create({
      baseURL: baseUrl,
      headers: {
        'X-API-Key': apiKey
      },
      timeout: 300000 // 5 minutes for long operations
    });
  }

  // Health check
  async healthCheck() {
    const response = await this.client.get('/health');
    return response.data;
  }

  // YouTube to MP3 conversion
  async youtubeToMp3(url, options = {}) {
    const payload = {
      url,
      audio_quality: options.audioQuality ?? 0,
      audio_format: options.audioFormat ?? 'mp3',
      extract_metadata: options.extractMetadata ?? true
    };
    
    const response = await this.client.post('/api/v1/youtube-to-mp3', payload, {
      headers: { 'Content-Type': 'application/json' }
    });
    return response.data;
  }

  // Stem separation
  async separateStems(filePath, options = {}) {
    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));
    
    if (options.model) form.append('model', options.model);
    if (options.outputFormat) form.append('output_format', options.outputFormat);
    if (options.stems) form.append('stems', options.stems.join(','));
    
    const response = await this.client.post('/api/v1/separate-stems', form, {
      headers: form.getHeaders()
    });
    return response.data;
  }

  // Download file
  async downloadFile(downloadUrl, outputPath) {
    const response = await this.client.get(downloadUrl, {
      responseType: 'stream'
    });
    
    const writer = fs.createWriteStream(outputPath);
    response.data.pipe(writer);
    
    return new Promise((resolve, reject) => {
      writer.on('finish', () => resolve(outputPath));
      writer.on('error', reject);
    });
  }
}

module.exports = MusicToolsAPI;
```

---

## API Endpoints

### Health Check

Check if the API is operational.

**Endpoint:** `GET /health`

```javascript
const MusicToolsAPI = require('./musicToolsApi');

const api = new MusicToolsAPI('your-api-key');

async function checkHealth() {
  try {
    const health = await api.healthCheck();
    console.log('API Status:', health);
    // Output: { status: 'healthy', service: 'music-tools-api', version: '1.0.0' }
  } catch (error) {
    console.error('API is not available:', error.message);
  }
}

checkHealth();
```

---

### YouTube to MP3

Convert a YouTube video to an audio file.

**Endpoint:** `POST /api/v1/youtube-to-mp3`

#### Request Body

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `url` | string | ✅ | - | YouTube video URL |
| `audio_quality` | number | ❌ | 0 | Quality: 0 (best) to 10 (smallest) |
| `audio_format` | string | ❌ | "mp3" | Format: mp3, m4a, wav, flac, aac, opus |
| `extract_metadata` | boolean | ❌ | true | Extract video metadata |

#### Audio Quality Scale

| Value | Bitrate | File Size | Use Case |
|-------|---------|-----------|----------|
| 0 | ~320 kbps | Largest | High-fidelity audio |
| 5 | ~160 kbps | Medium | Balanced quality/size |
| 10 | ~64 kbps | Smallest | Streaming, previews |

#### Example: Basic Conversion

```javascript
const MusicToolsAPI = require('./musicToolsApi');
const api = new MusicToolsAPI('your-api-key');

async function convertYouTubeToMp3() {
  try {
    // Convert video to MP3
    const result = await api.youtubeToMp3(
      'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    );

    if (result.success) {
      console.log('Conversion successful!');
      console.log('File ID:', result.file_id);
      console.log('Filename:', result.filename);
      console.log('File Size:', result.file_size_mb, 'MB');
      console.log('Download URL:', result.download_url);
      
      if (result.metadata) {
        console.log('Title:', result.metadata.title);
        console.log('Duration:', result.metadata.duration, 'seconds');
        console.log('Uploader:', result.metadata.uploader);
      }

      // Download the file
      const outputPath = `./${result.filename}`;
      await api.downloadFile(result.download_url, outputPath);
      console.log('Downloaded to:', outputPath);
    } else {
      console.error('Conversion failed:', result.error);
    }
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

convertYouTubeToMp3();
```

#### Example: Custom Quality and Format

```javascript
async function convertWithOptions() {
  const result = await api.youtubeToMp3(
    'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    {
      audioQuality: 0,        // Best quality
      audioFormat: 'flac',    // Lossless format
      extractMetadata: true
    }
  );
  
  console.log(result);
}
```

#### Response Schema

```javascript
{
  "success": true,
  "message": "Audio downloaded successfully",
  "file_id": "abc123xyz",
  "filename": "Rick Astley - Never Gonna Give You Up.mp3",
  "file_size_mb": 3.45,
  "download_url": "/api/v1/download/abc123xyz",
  "metadata": {
    "title": "Rick Astley - Never Gonna Give You Up",
    "duration": 212,
    "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "uploader": "Rick Astley",
    "upload_date": "20091025",
    "view_count": 1500000000,
    "description": "Official music video..."
  }
}
```

---

### Stem Separation

Separate an audio file into individual stems (vocals, drums, bass, other).

**Endpoint:** `POST /api/v1/separate-stems`

#### Request (multipart/form-data)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file` | file | ✅ | - | Audio file (MP3, WAV, FLAC, M4A) |
| `model` | string | ❌ | "htdemucs" | Demucs model |
| `output_format` | string | ❌ | "wav" | Output format: wav, mp3, flac |
| `stems` | string | ❌ | all | Comma-separated: vocals,drums,bass,other |

#### Available Models

| Model | Quality | Speed | Description |
|-------|---------|-------|-------------|
| `htdemucs` | Good | Fast | Default, balanced |
| `htdemucs_ft` | Better | Slower | Fine-tuned version |
| `mdx_extra` | Best | Slowest | Highest quality |

#### Example: Basic Stem Separation

```javascript
const MusicToolsAPI = require('./musicToolsApi');
const api = new MusicToolsAPI('your-api-key');

async function separateStems() {
  try {
    const result = await api.separateStems('./song.mp3');

    if (result.success) {
      console.log('Separation successful!');
      console.log('Job ID:', result.job_id);
      console.log('Processing time:', result.processing_time_seconds, 'seconds');
      console.log('Stems:', result.stems);

      // Download each stem
      if (result.stems.vocals) {
        await api.downloadFile(result.stems.vocals, './vocals.wav');
        console.log('Downloaded vocals');
      }
      if (result.stems.drums) {
        await api.downloadFile(result.stems.drums, './drums.wav');
        console.log('Downloaded drums');
      }
      if (result.stems.bass) {
        await api.downloadFile(result.stems.bass, './bass.wav');
        console.log('Downloaded bass');
      }
      if (result.stems.other) {
        await api.downloadFile(result.stems.other, './other.wav');
        console.log('Downloaded other');
      }
    } else {
      console.error('Separation failed:', result.error);
    }
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

separateStems();
```

#### Example: Extract Only Vocals

```javascript
async function extractVocalsOnly() {
  const result = await api.separateStems('./song.mp3', {
    model: 'htdemucs_ft',     // Better quality model
    outputFormat: 'mp3',      // MP3 output
    stems: ['vocals']         // Only extract vocals
  });

  if (result.success && result.stems.vocals) {
    await api.downloadFile(result.stems.vocals, './vocals.mp3');
    console.log('Vocals extracted successfully!');
  }
}
```

#### Example: Create Karaoke (Instrumental)

```javascript
async function createKaraoke() {
  // Extract drums, bass, and other (everything except vocals)
  const result = await api.separateStems('./song.mp3', {
    stems: ['drums', 'bass', 'other'],
    outputFormat: 'wav'
  });

  if (result.success) {
    // Download instrumental parts
    const instrumentals = ['drums', 'bass', 'other'];
    for (const stem of instrumentals) {
      if (result.stems[stem]) {
        await api.downloadFile(result.stems[stem], `./${stem}.wav`);
      }
    }
    console.log('Karaoke tracks ready! Mix drums, bass, and other together.');
  }
}
```

#### Response Schema

```javascript
{
  "success": true,
  "message": "Stems separated successfully",
  "job_id": "job_xyz123",
  "stems": {
    "vocals": "/api/v1/download/job_xyz123/vocals.wav",
    "drums": "/api/v1/download/job_xyz123/drums.wav",
    "bass": "/api/v1/download/job_xyz123/bass.wav",
    "other": "/api/v1/download/job_xyz123/other.wav"
  },
  "processing_time_seconds": 45.2
}
```

---

### File Download

Download converted audio files or separated stems.

**Endpoints:**
- `GET /api/v1/download/{file_id}` — Download converted audio
- `GET /api/v1/download/{job_id}/{filename}` — Download specific stem

#### Example: Download with Progress

```javascript
const axios = require('axios');
const fs = require('fs');

async function downloadWithProgress(api, downloadUrl, outputPath) {
  const response = await api.client.get(downloadUrl, {
    responseType: 'stream'
  });

  const totalLength = response.headers['content-length'];
  let downloadedLength = 0;

  const writer = fs.createWriteStream(outputPath);

  response.data.on('data', (chunk) => {
    downloadedLength += chunk.length;
    const progress = ((downloadedLength / totalLength) * 100).toFixed(1);
    process.stdout.write(`\rDownloading: ${progress}%`);
  });

  response.data.pipe(writer);

  return new Promise((resolve, reject) => {
    writer.on('finish', () => {
      console.log('\nDownload complete!');
      resolve(outputPath);
    });
    writer.on('error', reject);
  });
}

// Usage
await downloadWithProgress(api, '/api/v1/download/abc123', './song.mp3');
```

---

## Complete Integration Example

A full example showing a complete workflow:

```javascript
// example-integration.js
const MusicToolsAPI = require('./musicToolsApi');
const path = require('path');

const API_KEY = process.env.MUSIC_TOOLS_API_KEY || 'your-api-key';
const api = new MusicToolsAPI(API_KEY);

async function main() {
  try {
    // 1. Check API health
    console.log('🔍 Checking API health...');
    const health = await api.healthCheck();
    console.log('✅ API Status:', health.status);

    // 2. Convert YouTube video to MP3
    console.log('\n🎵 Converting YouTube video to MP3...');
    const youtubeUrl = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ';
    
    const conversionResult = await api.youtubeToMp3(youtubeUrl, {
      audioQuality: 0,
      audioFormat: 'mp3'
    });

    if (!conversionResult.success) {
      throw new Error(`Conversion failed: ${conversionResult.error}`);
    }

    console.log('✅ Conversion successful!');
    console.log(`   Title: ${conversionResult.metadata?.title}`);
    console.log(`   Size: ${conversionResult.file_size_mb} MB`);

    // 3. Download the converted file
    console.log('\n📥 Downloading MP3...');
    const mp3Path = './downloaded_song.mp3';
    await api.downloadFile(conversionResult.download_url, mp3Path);
    console.log(`✅ Downloaded to: ${mp3Path}`);

    // 4. Separate stems from the downloaded file
    console.log('\n🎛️ Separating stems...');
    const stemResult = await api.separateStems(mp3Path, {
      model: 'htdemucs',
      outputFormat: 'wav',
      stems: ['vocals', 'drums', 'bass', 'other']
    });

    if (!stemResult.success) {
      throw new Error(`Stem separation failed: ${stemResult.error}`);
    }

    console.log('✅ Stem separation successful!');
    console.log(`   Processing time: ${stemResult.processing_time_seconds}s`);

    // 5. Download all stems
    console.log('\n📥 Downloading stems...');
    const stems = ['vocals', 'drums', 'bass', 'other'];
    
    for (const stem of stems) {
      if (stemResult.stems[stem]) {
        const stemPath = `./${stem}.wav`;
        await api.downloadFile(stemResult.stems[stem], stemPath);
        console.log(`   ✅ Downloaded ${stem}.wav`);
      }
    }

    console.log('\n🎉 All done! Files created:');
    console.log('   - downloaded_song.mp3');
    console.log('   - vocals.wav');
    console.log('   - drums.wav');
    console.log('   - bass.wav');
    console.log('   - other.wav');

  } catch (error) {
    console.error('❌ Error:', error.response?.data?.error || error.message);
    process.exit(1);
  }
}

main();
```

---

## Error Handling

### Error Response Format

```javascript
{
  "success": false,
  "error": "Error description",
  "details": {
    "field": "Additional context"
  }
}
```

### Common Errors

| Status Code | Error | Solution |
|-------------|-------|----------|
| 401 | Invalid API key | Check your X-API-Key header |
| 400 | Invalid URL | Ensure URL is a valid YouTube link |
| 400 | Unsupported format | Use supported formats (mp3, wav, etc.) |
| 413 | File too large | Reduce file size (max ~200MB) |
| 429 | Rate limit exceeded | Wait and retry with exponential backoff |
| 500 | Server error | Retry or contact support |

### Robust Error Handling

```javascript
async function safeApiCall(apiFunction, ...args) {
  const maxRetries = 3;
  let lastError;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await apiFunction(...args);
    } catch (error) {
      lastError = error;
      
      const status = error.response?.status;
      const errorMessage = error.response?.data?.error || error.message;
      
      console.error(`Attempt ${attempt}/${maxRetries} failed: ${errorMessage}`);

      // Don't retry client errors (except rate limiting)
      if (status >= 400 && status < 500 && status !== 429) {
        throw error;
      }

      // Rate limiting - wait longer
      if (status === 429) {
        const waitTime = Math.pow(2, attempt) * 5000; // 5s, 10s, 20s
        console.log(`Rate limited. Waiting ${waitTime/1000}s...`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
        continue;
      }

      // Server errors - exponential backoff
      if (attempt < maxRetries) {
        const waitTime = Math.pow(2, attempt) * 1000;
        console.log(`Retrying in ${waitTime/1000}s...`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }
  }

  throw lastError;
}

// Usage
const result = await safeApiCall(
  api.youtubeToMp3.bind(api),
  'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
);
```

---

## Rate Limiting

The API enforces rate limits to ensure fair usage:

| Operation Type | Limit |
|----------------|-------|
| Light operations (health, download) | Higher limit |
| Heavy operations (convert, separate) | Lower limit |

### Handling Rate Limits

```javascript
async function withRateLimitHandling(apiCall) {
  try {
    return await apiCall();
  } catch (error) {
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after'] || 60;
      console.log(`Rate limited. Waiting ${retryAfter} seconds...`);
      await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
      return await apiCall(); // Retry once
    }
    throw error;
  }
}

// Usage
const result = await withRateLimitHandling(() => 
  api.youtubeToMp3('https://www.youtube.com/watch?v=...')
);
```

---

## Best Practices

### 1. Store API Key Securely

```javascript
// Use environment variables
const API_KEY = process.env.MUSIC_TOOLS_API_KEY;

// Never hardcode in source code
// const API_KEY = 'abc123'; // ❌ DON'T DO THIS
```

### 2. Set Appropriate Timeouts

```javascript
const api = new MusicToolsAPI(apiKey);
api.client.defaults.timeout = 300000; // 5 minutes for stem separation
```

### 3. Clean Up Downloaded Files

```javascript
const fs = require('fs').promises;

async function processAndCleanup(youtubeUrl) {
  const tempFiles = [];
  
  try {
    const result = await api.youtubeToMp3(youtubeUrl);
    const mp3Path = './temp_song.mp3';
    await api.downloadFile(result.download_url, mp3Path);
    tempFiles.push(mp3Path);
    
    // Process the file...
    
  } finally {
    // Clean up temp files
    for (const file of tempFiles) {
      try {
        await fs.unlink(file);
      } catch (e) {
        // Ignore cleanup errors
      }
    }
  }
}
```

### 4. Use Streaming for Large Files

```javascript
async function streamLargeFile(downloadUrl, outputPath) {
  const response = await api.client.get(downloadUrl, {
    responseType: 'stream',
    maxContentLength: Infinity,
    maxBodyLength: Infinity
  });
  
  const writer = fs.createWriteStream(outputPath);
  response.data.pipe(writer);
  
  return new Promise((resolve, reject) => {
    writer.on('finish', resolve);
    writer.on('error', reject);
  });
}
```

### 5. Validate Input Before Sending

```javascript
function isValidYouTubeUrl(url) {
  const patterns = [
    /^(https?:\/\/)?(www\.)?youtube\.com\/watch\?v=[\w-]+/,
    /^(https?:\/\/)?youtu\.be\/[\w-]+/,
    /^(https?:\/\/)?music\.youtube\.com\/watch\?v=[\w-]+/
  ];
  return patterns.some(pattern => pattern.test(url));
}

async function convertSafely(url) {
  if (!isValidYouTubeUrl(url)) {
    throw new Error('Invalid YouTube URL');
  }
  return await api.youtubeToMp3(url);
}
```

---

## Support

- **API Documentation:** https://apitools.bahar.co.il/docs (available in development mode only)
- **OpenAPI Schema:** https://apitools.bahar.co.il/openapi.json (available in development mode only)
- **ReDoc:** https://apitools.bahar.co.il/redoc (available in development mode only)

**Note:** In production, interactive documentation endpoints are disabled when `DEBUG=false` for security. Use this client library or the examples in this guide instead.
