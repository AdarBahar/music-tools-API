# Stems Parameter Default Behavior Update

## Overview

Updated the stem separation API to make the `stems` parameter default to all available stems when empty, null, or omitted. This improves the user experience by eliminating the need to explicitly specify all stems for full separation.

## Changes Made

### 1. API Route Update (`app/api/routes/stems.py`)

**Before:**
- Empty or null `stems` parameter would result in no stems being processed
- Users had to explicitly specify `stems=vocals,drums,bass,other` for full separation

**After:**
- Empty, null, or omitted `stems` parameter defaults to all stems (`vocals,drums,bass,other`)
- Explicit specification is only needed for partial separation

### 2. Enhanced Parameter Parsing

The API now handles these cases for the `stems` parameter:

| Input | Behavior | Result |
|-------|----------|--------|
| `None` | Default to all stems | `['vocals', 'drums', 'bass', 'other']` |
| `""` (empty string) | Default to all stems | `['vocals', 'drums', 'bass', 'other']` |
| `"   "` (whitespace) | Default to all stems | `['vocals', 'drums', 'bass', 'other']` |
| `"vocals"` | Extract specified stem | `['vocals']` |
| `"vocals,drums"` | Extract specified stems | `['vocals', 'drums']` |
| `"vocals,,drums"` | Ignore empty values | `['vocals', 'drums']` |
| `" vocals , drums "` | Trim whitespace | `['vocals', 'drums']` |

### 3. Validation

- Invalid stem names are still rejected with clear error messages
- Valid stems: `vocals`, `drums`, `bass`, `other`
- Case-sensitive validation maintained

## API Usage Examples

### Default Behavior (All Stems)

```bash
# All of these extract all stems:

# Method 1: Omit stems parameter
curl -X POST "http://localhost:8000/api/v1/separate-stems" \
  -F "file=@audio.mp3" \
  -F "model=htdemucs"

# Method 2: Empty stems parameter
curl -X POST "http://localhost:8000/api/v1/separate-stems" \
  -F "file=@audio.mp3" \
  -F "model=htdemucs" \
  -F "stems="

# Method 3: Explicit all stems (same result)
curl -X POST "http://localhost:8000/api/v1/separate-stems" \
  -F "file=@audio.mp3" \
  -F "model=htdemucs" \
  -F "stems=vocals,drums,bass,other"
```

### Partial Separation

```bash
# Extract only vocals
curl -X POST "http://localhost:8000/api/v1/separate-stems" \
  -F "file=@audio.mp3" \
  -F "stems=vocals"

# Extract vocals and drums
curl -X POST "http://localhost:8000/api/v1/separate-stems" \
  -F "file=@audio.mp3" \
  -F "stems=vocals,drums"
```

## Python Client Usage

```python
from music_tools_client import MusicToolsClient

client = MusicToolsClient()

# All of these extract all stems:
result1 = client.separate_stems("audio.mp3")  # stems=None (default)
result2 = client.separate_stems("audio.mp3", stems="")  # Empty string
result3 = client.separate_stems("audio.mp3", stems="vocals,drums,bass,other")  # Explicit

# Partial separation:
vocals_only = client.separate_stems("audio.mp3", stems="vocals")
vocals_drums = client.separate_stems("audio.mp3", stems="vocals,drums")
```

## Benefits

1. **Improved UX**: No need to remember and type all stem names for full separation
2. **Backward Compatibility**: Existing code with explicit stems continues to work
3. **Intuitive Behavior**: Empty/null parameter naturally defaults to "all"
4. **Reduced Errors**: Less chance of typos when specifying all stems
5. **Cleaner Examples**: Documentation examples are simpler and cleaner

## Testing

Created comprehensive test suite (`test_stems_default_behavior.py`) that verifies:
- ✅ Null input defaults to all stems
- ✅ Empty string defaults to all stems  
- ✅ Whitespace-only input defaults to all stems
- ✅ Valid specific stems are processed correctly
- ✅ Invalid stems are rejected with proper error messages
- ✅ Edge cases (empty values in list, extra whitespace) are handled

## Documentation Updates

Updated all documentation to reflect the new behavior:
- ✅ `README.md` - Updated parameter descriptions and examples
- ✅ `API_DOCUMENTATION.md` - Added detailed behavior section with examples
- ✅ `examples/curl_examples.sh` - Updated examples to show default behavior
- ✅ `examples/python_client.py` - Updated examples and docstrings
- ✅ `CHANGELOG.md` - Documented the change

## Migration Guide

### For Existing Users

**No action required** - existing code continues to work:
- Code that explicitly specifies `stems=vocals,drums,bass,other` works unchanged
- Code that specifies partial stems (e.g., `stems=vocals`) works unchanged

### For New Users

**Simplified usage** - just omit the stems parameter for full separation:
```bash
# Old way (still works)
curl -F "stems=vocals,drums,bass,other" ...

# New way (recommended)
curl ... # stems parameter omitted
```

## Implementation Details

The change is implemented in the API route layer (`app/api/routes/stems.py`) with enhanced parameter parsing logic that:

1. Checks if `stems` parameter exists and is non-empty after trimming
2. Splits comma-separated values and filters out empty strings
3. Validates each stem against the allowed list
4. Passes `None` to the service layer when no valid stems are specified
5. Service layer already had logic to default to all stems when `None` is passed

This ensures the change is contained to the API layer with minimal impact on the core separation logic.
