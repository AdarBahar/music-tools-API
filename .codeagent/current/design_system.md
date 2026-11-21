# Design System

## Project paths and deployment context

**UI State**: No web UI currently implemented  
**API Documentation**: Auto-generated via FastAPI at `/docs` endpoint  
**Client Interface**: REST API only, consumed via HTTP clients  

## Current Design Philosophy

The Music Tools API follows an API-first design approach:

- **REST API**: Clean, RESTful endpoint structure
- **OpenAPI Documentation**: Auto-generated interactive documentation
- **JSON Responses**: Consistent response format across all endpoints
- **Error Handling**: Structured error responses with appropriate HTTP status codes

## API Design Patterns

### Endpoint Structure
- **Base Path**: `/api/v1/`
- **Resource-Based**: `/youtube-to-mp3`, `/separate-stems`
- **Action-Oriented**: Clear endpoint purposes

### Response Format
Success responses use a flat model per route. Example: `YouTubeToMP3Response` in `app/models/responses.py`. The model has `success`, and the fields for that route.

### Error Format
Most errors use FastAPI's `detail` field:
```json
{
  "detail": "Error description"
}
```
Pipeline failures (download, separation) return the same body shape as a success, with `success: false` and an `error` string. The status code gives the cause (502, 500, 503, 507).

## Future UI Considerations

When a web UI is implemented:
- **Framework**: Consider React/Vue.js for interactive audio processing
- **Design Language**: Modern, clean interface focused on audio workflows
- **Progress Indication**: Real-time processing status and progress bars
- **File Management**: Upload/download interface with previews
- **Responsive**: Mobile-friendly design for accessibility

## Documentation Design

- **Interactive API Docs**: FastAPI Swagger UI at `/docs` (only when `DEBUG=true`)
- **Examples**: Comprehensive curl and Python client examples
- **Progressive Disclosure**: Basic to advanced usage patterns

## TODO: Web UI Design System

- [ ] Define color palette and typography
- [ ] Create component library
- [ ] Design file upload/processing workflows
- [ ] Audio player integration patterns