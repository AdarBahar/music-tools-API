# MP3 File Naming Convention Update

## Overview

Updated the file naming convention for both YouTube MP3 downloads and stem separation to use the video title as the base filename, as requested.

## Changes Made

### 1. YouTube MP3 Downloads

**Before:**
- Format: `{title}_{file_id}.{format}`
- Example: `Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)_abc123.mp3`

**After:**
- Format: `{title}.{format}`
- Example: `Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster).mp3`

### 2. Stem Separation

**Before:**
- Format: `{stem_name}.{format}`
- Example: `vocals.mp3`, `drums.mp3`, `bass.mp3`, `other.mp3`

**After:**
- Format: `{original_filename} - {stem_name}.{format}` (when original filename is available)
- Format: `{stem_name}.{format}` (fallback when no original filename)
- Example: `Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) - vocals.mp3`

## Implementation Details

### Files Modified

1. **`app/services/youtube_service.py`**
   - Updated `_generate_filename()` method
   - Removed file_id from filename
   - Increased character limit from 100 to 200 for full titles
   - Added support for additional safe characters: `.`, `(`, `)`

2. **`app/services/stem_service.py`**
   - Added `original_filename` parameter to `separate_stems()` method
   - Added `original_filename` parameter to `_process_stems()` method
   - Updated filename generation logic to use original filename with stem suffix

3. **`app/api/routes/stems.py`**
   - Updated stem separation endpoint to pass `file.filename` as `original_filename`

### Character Handling

The filename sanitization now allows these characters:
- Alphanumeric characters (a-z, A-Z, 0-9)
- Spaces
- Hyphens (-)
- Underscores (_)
- Periods (.)
- Parentheses ( )

Special characters like `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|` are removed for filesystem compatibility.

## Examples

### YouTube Download Examples

| Video Title | Generated Filename |
|-------------|-------------------|
| `Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)` | `Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster).mp3` |
| `The Beatles - Hey Jude` | `The Beatles - Hey Jude.mp3` |
| `Queen - Bohemian Rhapsody (Official Video)` | `Queen - Bohemian Rhapsody (Official Video).mp3` |

### Stem Separation Examples

For a file named `Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster).mp3`:

| Stem Type | Generated Filename |
|-----------|-------------------|
| Vocals | `Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) - vocals.mp3` |
| Drums | `Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) - drums.mp3` |
| Bass | `Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) - bass.mp3` |
| Other | `Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) - other.mp3` |

### Fallback Behavior

When no original filename is available (e.g., direct file upload without metadata), the system falls back to:
- `vocals.mp3`
- `drums.mp3`
- `bass.mp3`
- `other.mp3`

## Testing

Created `test_naming_convention.py` to verify the implementation:
- ✅ YouTube filename generation
- ✅ Stem filename generation with original filename
- ✅ Stem filename generation without original filename (fallback)
- ✅ Edge cases (special characters, long titles, no metadata)

All tests pass successfully.

## Backward Compatibility

This change affects the naming convention but does not break existing functionality:
- Existing files are not renamed
- API endpoints remain the same
- File download functionality is unchanged
- Only new downloads will use the updated naming convention

## Benefits

1. **Cleaner filenames**: No random file IDs in the filename
2. **Better organization**: Stems are clearly associated with their source file
3. **User-friendly**: Filenames are immediately recognizable
4. **Consistent**: Same naming pattern across YouTube downloads and stem separation
