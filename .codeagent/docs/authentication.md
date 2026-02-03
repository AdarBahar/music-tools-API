# 🔐 API Access Management Guide

The Music Tools API has a multi-layered access control system. Here's how to configure and manage access:

## 1. **API Key Authentication**

**Enable/Disable Authentication:**
```bash
# In .env file or environment variables
REQUIRE_API_KEY=true  # Enable authentication (default: false)
```

**Configure API Keys:**
```bash
# Set valid API keys (comma-separated)
VALID_API_KEYS="your-secret-key-1,your-secret-key-2,admin-key-xyz"
```

**Using API Keys:**
```bash
# Include in request headers
curl -H "X-API-Key: your-secret-key-1" \
     -X POST http://localhost:8000/api/v1/youtube-to-mp3 \
     -d '{"url": "https://youtube.com/watch?v=..."}'
```

## 2. **CORS (Cross-Origin) Access Control**

**Configure Allowed Origins:**
```bash
# Allow specific domains to access the API
ALLOWED_ORIGINS="https://yourapp.com,https://dashboard.yourapp.com,http://localhost:3000"
```

This controls which websites can make requests to your API from browsers.

## 3. **Rate Limiting**

**Enable Rate Limiting:**
```bash
ENABLE_RATE_LIMITING=true
RATE_LIMIT_STORAGE_URI=redis://localhost:6379/0
```

**Configure Rate Limits:**
```bash
# Requests per minute by operation type
RATE_LIMIT_HEAVY_OPERATIONS="3/minute"    # Stem separation, YouTube downloads  
RATE_LIMIT_LIGHT_OPERATIONS="20/minute"   # Downloads, model lists
RATE_LIMIT_INFO_OPERATIONS="60/minute"    # Health checks, info endpoints
```

## 4. **Complete Configuration Example**

Create a `.env` file in your project root:

```bash
# Security Configuration
REQUIRE_API_KEY=true
VALID_API_KEYS="prod-key-123,dev-key-456,admin-key-789"
ALLOWED_ORIGINS="https://yourapp.com,https://api.yourapp.com"

# Rate Limiting 
ENABLE_RATE_LIMITING=true
REDIS_URL=redis://localhost:6379/0
RATE_LIMIT_HEAVY_OPERATIONS="5/minute"
RATE_LIMIT_LIGHT_OPERATIONS="30/minute" 
RATE_LIMIT_INFO_OPERATIONS="100/minute"

# Timeout Configuration
API_REQUEST_TIMEOUT=120
YOUTUBE_DOWNLOAD_TIMEOUT=600
STEM_SEPARATION_TIMEOUT=1800
```

## 5. **Access Management Strategies**

### 🔒 Production Security (Recommended):
```bash
REQUIRE_API_KEY=true
VALID_API_KEYS="secure-production-key-abc123"
ALLOWED_ORIGINS="https://yourdomain.com"
ENABLE_RATE_LIMITING=true
RATE_LIMIT_HEAVY_OPERATIONS="3/minute"
```

### 🧪 Development Mode:
```bash
REQUIRE_API_KEY=false  # No authentication needed
ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8080"
ENABLE_RATE_LIMITING=false  # No rate limits
```

### 🏢 Multi-Client Setup:
```bash
REQUIRE_API_KEY=true
VALID_API_KEYS="client1-key,client2-key,admin-key,mobile-app-key"
ALLOWED_ORIGINS="https://client1.com,https://client2.com,https://admin.com"
RATE_LIMIT_HEAVY_OPERATIONS="10/minute"  # Higher limits
```

## 6. **Monitoring Access**

### Security Event Logging:
The API automatically logs:
- Authentication failures
- Invalid API key attempts  
- Rate limit violations
- Unusual access patterns

### Health Check Monitoring:
```bash
curl http://localhost:8000/health
```

### Metrics Monitoring:
```bash 
curl http://localhost:8000/metrics  # Prometheus metrics
```

## 7. **Client Integration Examples**

### JavaScript (with API key):
```javascript
const response = await fetch('/api/v1/youtube-to-mp3', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-api-key'
  },
  body: JSON.stringify({
    url: 'https://youtube.com/watch?v=...',
    audio_quality: 0
  })
});
```

### Python Client:
```python
import requests

headers = {'X-API-Key': 'your-api-key'}
data = {
    'url': 'https://youtube.com/watch?v=...',
    'audio_quality': 0
}

response = requests.post(
    'http://localhost:8000/api/v1/youtube-to-mp3',
    json=data, 
    headers=headers
)
```

### cURL Examples:
```bash
# YouTube to MP3 with authentication
curl -X POST "http://localhost:8000/api/v1/youtube-to-mp3" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "audio_quality": 0,
    "audio_format": "mp3"
  }'

# Stem separation with authentication
curl -X POST "http://localhost:8000/api/v1/separate-stems" \
  -H "X-API-Key: your-api-key" \
  -F "file=@audio.mp3" \
  -F "model=htdemucs" \
  -F "output_format=wav"
```

## 8. **Security Features**

### Authentication System:
- ✅ **API Key-based authentication** with configurable requirement
- ✅ **Multiple API keys support** for different clients/users
- ✅ **Automatic security event logging** for failed attempts
- ✅ **Flexible header-based authentication** (`X-API-Key`)

### Access Control:
- ✅ **CORS configuration** with specific allowed origins
- ✅ **Rate limiting** with Redis backend for distributed environments
- ✅ **Tiered rate limits** for different operation types
- ✅ **Client identification** using API keys or IP addresses

### Monitoring & Logging:
- ✅ **Comprehensive security logging** with client IP and user agent
- ✅ **Authentication failure tracking** with request context
- ✅ **Prometheus metrics** for access patterns and security events
- ✅ **Health check endpoint** for monitoring system integration

## 9. **Security Best Practices**

### ✅ Production Deployment:
- **Always use HTTPS** in production environments
- **Generate long, random API keys** (minimum 32 characters)
- **Rotate API keys regularly** (monthly or quarterly)
- **Use specific CORS origins** (avoid wildcards like `*`)
- **Enable rate limiting** to prevent abuse and DoS attacks
- **Monitor security logs** for unusual activity patterns
- **Use Redis for distributed rate limiting** in multi-instance deployments

### ✅ API Key Management:
- Store API keys securely (environment variables, not code)
- Use different keys for different environments (dev/staging/prod)
- Implement key expiration and rotation policies
- Log all key usage for audit purposes
- Revoke compromised keys immediately

### ✅ Network Security:
- Deploy behind a reverse proxy (nginx, Apache)
- Use SSL/TLS certificates for HTTPS
- Configure firewall rules to limit access
- Consider VPN or IP whitelisting for sensitive deployments
- Implement DDoS protection at the infrastructure level

## 10. **Troubleshooting Access Issues**

### Common Authentication Errors:

**401 Unauthorized - Missing API Key:**
```json
{
  "detail": "API key required. Provide X-API-Key header."
}
```
**Solution:** Add `X-API-Key` header with valid key

**401 Unauthorized - Invalid API Key:**
```json
{
  "detail": "Invalid API key"
}
```
**Solution:** Check that the API key is in `VALID_API_KEYS` environment variable

**429 Too Many Requests - Rate Limited:**
```json
{
  "detail": "Rate limit exceeded: 3 per 1 minute"
}
```
**Solution:** Reduce request frequency or increase rate limits

**403 Forbidden - CORS Error:**
```
Access to fetch blocked by CORS policy
```
**Solution:** Add your domain to `ALLOWED_ORIGINS` configuration

### Debug Mode:
```bash
# Enable debug logging to troubleshoot issues
LOG_LEVEL=DEBUG
```

This comprehensive access management system ensures your Music Tools API is secure, scalable, and properly monitored in production environments.