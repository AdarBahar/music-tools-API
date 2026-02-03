#!/usr/bin/env python3
"""
Test script to validate authentication implementation
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

# Test imports
try:
    from app.core.config import Settings
    print("✅ Config import successful")
    
    # Test settings instantiation
    settings = Settings()
    print(f"✅ Settings loaded - REQUIRE_API_KEY: {settings.REQUIRE_API_KEY}")
    print(f"✅ API_KEY_HEADER: {settings.API_KEY_HEADER}")
    print(f"✅ ALLOWED_ORIGINS: {settings.ALLOWED_ORIGINS}")
    
except ImportError as e:
    print(f"❌ Config import failed: {e}")
    sys.exit(1)

try:
    from app.core.auth import verify_api_key, AuthenticationError
    print("✅ Auth module import successful")
except ImportError as e:
    print(f"❌ Auth import failed: {e}")
    sys.exit(1)

try:
    from app.api.routes import youtube, stems, downloads
    print("✅ Routes import successful")
except ImportError as e:
    print(f"❌ Routes import failed: {e}")
    sys.exit(1)

try:
    import main
    print("✅ Main module import successful")
    print("✅ FastAPI app created successfully")
except ImportError as e:
    print(f"❌ Main import failed: {e}")
    sys.exit(1)

print("\n🎉 All authentication components loaded successfully!")
print("\n📋 Authentication Status:")
print(f"   - API Key Required: {settings.REQUIRE_API_KEY}")
print(f"   - Valid API Keys: {len(settings.VALID_API_KEYS)} configured")
print(f"   - CORS Origins: {len(settings.ALLOWED_ORIGINS)} configured")

print("\n🔒 To enable authentication:")
print("   1. Set REQUIRE_API_KEY=true in .env")
print("   2. Set VALID_API_KEYS=key1,key2 in .env")
print("   3. Set ALLOWED_ORIGINS=https://yourdomain.com in .env")

print("\n🧪 Test with curl:")
print('   curl -H "X-API-Key: your-key" http://localhost:8000/api/v1/youtube-to-mp3')