# Memory Log

Durable knowledge and key decisions for the Music Tools API project.

## Architecture Decisions

- **FastAPI over Flask**: Chosen for async support, automatic OpenAPI docs, and modern Python features
- **Demucs Models**: Using Meta's Demucs for stem separation due to superior quality vs alternatives
- **Redis + Celery**: Background task processing for long-running audio operations
- **Docker Deployment**: Containerized for consistent deployment across environments

## Naming Conventions

- **Clean Filenames**: Use video titles for output files, not random UUIDs
- **Smart Stem Naming**: Preserve original filename with instrument suffix (e.g., `song_vocals.mp3`)
- **API Versioning**: `/api/v1/` prefix for all endpoints

## Model Selection

- **htdemucs**: Default model, best balance of quality and speed
- **htdemucs_ft**: Fine-tuned variant for specific use cases
- **mdx_extra**: Higher quality, slower processing
- **mdx_extra_q**: Quantized version for faster inference

## Quality Settings

- **Audio Quality Scale**: 0-10 where 0=best quality, 10=worst quality
- **Default Quality**: 0 (best) for professional use cases
- **Format Support**: Comprehensive (mp3, wav, flac, m4a, aac, opus)

## File Management Strategy

- **Automatic Cleanup**: 48-hour retention by default
- **Volume Persistence**: Data survives container restarts
- **Size Limits**: 100MB default to prevent abuse

## Performance Optimizations

- **GPU Support**: Available for 3-5x faster processing
- **Async Operations**: Non-blocking API endpoints
- **Background Processing**: Long operations don't block API responses

## CodeAgent Integration

- **Documentation-Driven**: Use `.codeagent/prompts/` for consistent AI workflows
- **State Tracking**: Maintain current project context in `.codeagent/current/`
- **Planning**: Leverage AI prompts for feature planning and implementation