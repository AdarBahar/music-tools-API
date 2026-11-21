# Changelog

All notable changes to the Music Tools API project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- YouTube files are stored as `<file_id> - <title>.<ext>`. The download link works again. The user still sees the clean title as the file name.
- Rate limits now apply. All routes use one shared limiter (`app/core/rate_limit.py`).
- Blocking downloads and Demucs runs no longer stop the event loop.
- A YouTube URL with an unsupported path or query parameter returns 400. A URL on another host returns 422. Neither returns 500. Links with `feature`, `ab_channel` and `si` parameters, and `music.youtube.com` links, are accepted.
- A YouTube link with `list=` downloads one video, not the full playlist.
- `MAX_FILE_SIZE_MB` and `REDIS_URL` now change the values that depend on them.
- The `/download/{file_id}/info` route is reachable.
- Stem output names are sanitized. Names with dots or symbols no longer fail after a long job, and a name cannot leave the job directory.
- Demucs errors and server paths no longer reach the client.
- Metric labels use route templates. The number of series no longer grows with each request.
- The key comparison is constant-time.
- The compose service name matches the Nginx upstream. `psutil`, `slowapi` and `prometheus-client` are in the core dependency lists.
- The `mdx_extra_q` model works with the default requirements. The `demucs[quantized]` extra is now a dependency.
- Removed the unused Celery dependency and the `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` settings. Redis is used for rate limit storage only. Set `REDIS_URL` as before.

### Changed
- `GET /api/v1/download/{file_id}/info` returns `created_at` as an ISO 8601 UTC time (for example `2021-10-18T14:11:30Z`). It was an epoch number in a string.
- Pydantic V2 style: `@field_validator`, `json_schema_extra` and `SettingsConfigDict`. The deprecation warnings are gone. `/health` uses a timezone-aware timestamp. The value now ends with `+00:00`. A monitor that parses the old format must accept this suffix.
- The three old print scripts in the repository root are removed. The new `tests/test_models.py` checks the request models.
- The one-time report files moved to `docs/`.
- **BREAKING**: Failed operations return an error HTTP status with the same body shape: 502 (download failed), 500 (separation failed), 503 with `Retry-After` (server busy or low memory), 507 (disk full).
- Old files are removed by the periodic cleanup job only. They live 48 to 72 hours.
- Browser cookies for yt-dlp are off by default. Set `YOUTUBE_COOKIES_FROM_BROWSER` to turn them on.
- **BREAKING**: Updated file naming convention for better organization
  - YouTube downloads now use video title as filename (no random IDs)
  - Stem files now include original filename with stem suffix
  - Example: `Song Title.mp3` → `Song Title - vocals.mp3`
- Increased filename character limit from 100 to 200 characters
- Enhanced character sanitization for better filesystem compatibility
- **Improved**: Stems parameter now defaults to all stems when empty or null
  - No need to specify `stems=vocals,drums,bass,other` for full separation
  - Empty string, null, or omitted parameter extracts all stems by default
- The API description and the root endpoint no longer claim Celery or progress tracking. Downloads and separations run in worker threads.

### Security
- **BREAKING**: Removed the unauthenticated `/static` mount. Use `/api/v1/download/...`.
- **BREAKING**: `/metrics` needs the `X-API-Key` header when `REQUIRE_API_KEY=true`.
- `/health` shows status only to callers without a valid key. The Redis password is always hidden.

### Added
- Comprehensive test suite for filename generation
- Comprehensive test suite for stems parameter default behavior
- Detailed documentation for new naming convention
- Enhanced API documentation with stems parameter behavior examples

## [1.0.0] - 2026-11-21

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
- Background task processing (Celery is listed as a dependency. The current code does not use it.)
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

## Planned

- Playlist download support
- Additional audio formats
- Advanced stem separation options
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
