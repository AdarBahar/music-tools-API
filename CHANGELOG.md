# Changelog

All notable changes to the Music Tools API project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **BREAKING**: Updated file naming convention for better organization
  - YouTube downloads now use video title as filename (no random IDs)
  - Stem files now include original filename with stem suffix
  - Example: `Song Title.mp3` → `Song Title - vocals.mp3`
- Increased filename character limit from 100 to 200 characters
- Enhanced character sanitization for better filesystem compatibility
- **Improved**: Stems parameter now defaults to all stems when empty or null
  - No need to specify `stems=vocals,drums,bass,other` for full separation
  - Empty string, null, or omitted parameter extracts all stems by default

### Added
- Comprehensive test suite for filename generation
- Comprehensive test suite for stems parameter default behavior
- Detailed documentation for new naming convention
- Enhanced API documentation with stems parameter behavior examples

## [1.0.0] - 2024-01-XX

### Added
- Initial release of Music Tools API as a standalone project
- YouTube to MP3 conversion functionality
  - Support for multiple audio formats (mp3, m4a, wav, flac, aac, opus)
  - Configurable audio quality (0-10 scale)
  - Automatic metadata extraction (title, duration, thumbnail, uploader)
  - Real-time progress tracking
- AI-powered audio stem separation using Meta's Demucs
  - Support for multiple Demucs models (htdemucs, htdemucs_ft, mdx_extra, mdx_extra_q)
  - Separation into vocals, drums, bass, and other instruments
  - Configurable output formats (wav, mp3, flac)
  - GPU acceleration support
- RESTful API with FastAPI framework
  - Automatic OpenAPI documentation (Swagger UI and ReDoc)
  - Comprehensive error handling and validation
  - File upload and download endpoints
- Docker containerization
  - Multi-service Docker Compose setup
  - Redis integration for background tasks
  - Nginx reverse proxy configuration
- Background task processing with Celery
- Automatic file cleanup system
- Health check endpoints
- Comprehensive logging
- Environment-based configuration

### Features
- **YouTube Integration**
  - Video information extraction without download
  - Support for various YouTube URL formats
  - Metadata preservation in downloaded files
  
- **Audio Processing**
  - High-quality audio extraction
  - Format conversion using FFmpeg
  - Batch processing capabilities
  
- **File Management**
  - Secure file handling with unique identifiers
  - Automatic cleanup of temporary and old files
  - Configurable file retention policies
  
- **API Features**
  - CORS support for web applications
  - Comprehensive error responses
  - File size validation
  - Progress tracking for long operations

### Documentation
- Complete API documentation with examples
- Docker deployment guide
- Manual installation instructions
- Configuration reference
- Performance optimization notes
- Contributing guidelines

### Security
- Input validation and sanitization
- Secure file path handling
- Optional API key authentication
- Resource usage limits

### Performance
- Async/await for I/O operations
- Efficient memory usage for large files
- GPU acceleration for AI models
- Configurable resource limits

## [Unreleased]

### Planned Features
- Playlist download support
- Additional audio formats
- Advanced stem separation options
- Rate limiting
- User authentication
- Webhook notifications
- Batch API endpoints
- Audio analysis features

---

## Version History

- **1.0.0**: Initial standalone release with core functionality
- **Future releases**: Will follow semantic versioning

## Migration Notes

This is the first standalone release. If migrating from a previous integrated version:

1. Update configuration files to use new environment variables
2. Install dependencies from the new requirements.txt
3. Update any custom integrations to use the new API endpoints
4. Review and update Docker configurations if using containerization

## Support

For questions about changes or upgrade assistance:
- Check the [README](README.md) for current documentation
- Review [API Documentation](API_DOCUMENTATION.md) for endpoint changes
- Open an issue on GitHub for specific problems
