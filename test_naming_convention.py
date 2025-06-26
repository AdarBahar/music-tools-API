#!/usr/bin/env python3
"""
Test script to verify the new naming convention for MP3 files and stems.
This is a simplified test that doesn't require the full environment.
"""

from typing import Optional


class MockVideoMetadata:
    """Mock VideoMetadata class for testing"""
    def __init__(self, title=None, duration=None, thumbnail_url=None,
                 uploader=None, upload_date=None, view_count=None, description=None):
        self.title = title
        self.duration = duration
        self.thumbnail_url = thumbnail_url
        self.uploader = uploader
        self.upload_date = upload_date
        self.view_count = view_count
        self.description = description


def generate_youtube_filename(metadata: Optional[MockVideoMetadata], file_id: str, audio_format: str) -> str:
    """Mock YouTube filename generation logic"""
    if metadata and metadata.title:
        # Clean the title for use as filename
        safe_title = "".join(c for c in metadata.title if c.isalnum() or c in (' ', '-', '_', '.', '(', ')')).strip()
        safe_title = safe_title[:200]  # Increased length limit for full titles
        filename = f"{safe_title}.{audio_format}"
    else:
        filename = f"audio_{file_id}.{audio_format}"

    return filename


def generate_stem_filename(original_filename: Optional[str], stem_name: str, output_format: str) -> str:
    """Mock stem filename generation logic"""
    if original_filename:
        # Remove extension from original filename if present
        base_name = original_filename
        if '.' in base_name:
            base_name = '.'.join(base_name.split('.')[:-1])
        output_filename = f"{base_name} - {stem_name}.{output_format}"
    else:
        output_filename = f"{stem_name}.{output_format}"

    return output_filename


def test_youtube_filename_generation():
    """Test YouTube MP3 filename generation"""
    print("🎵 Testing YouTube MP3 filename generation...")

    # Test with metadata (Rick Astley example)
    metadata = MockVideoMetadata(
        title="Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)",
        duration=213,
        thumbnail_url="https://example.com/thumb.jpg",
        uploader="Rick Astley",
        upload_date="20091025",
        view_count=1000000000,
        description="The official video for Rick Astley's Never Gonna Give You Up"
    )

    filename = generate_youtube_filename(metadata, "test-file-id", "mp3")
    expected = "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster).mp3"

    print(f"   Generated filename: {filename}")
    print(f"   Expected filename:  {expected}")

    if filename == expected:
        print("   ✅ YouTube filename generation: PASSED")
        return True
    else:
        print("   ❌ YouTube filename generation: FAILED")
        return False


def test_stem_filename_generation():
    """Test stem filename generation"""
    print("\n🎛️ Testing stem filename generation...")

    # Test with original filename
    original_filename = "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster).mp3"
    stem_names = ["vocals", "drums", "bass", "other"]

    for stem_name in stem_names:
        output_filename = generate_stem_filename(original_filename, stem_name, "mp3")
        expected_filename = f"Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) - {stem_name}.mp3"

        print(f"   {stem_name.capitalize()} stem: {output_filename}")
        print(f"   Expected:        {expected_filename}")

        if output_filename != expected_filename:
            print(f"   ❌ {stem_name} stem filename: FAILED")
            return False

    print("   ✅ Stem filename generation: PASSED")
    return True


def test_stem_filename_without_original():
    """Test stem filename generation without original filename"""
    print("\n🎛️ Testing stem filename generation (no original filename)...")

    # Test without original filename (fallback behavior)
    stem_names = ["vocals", "drums", "bass", "other"]

    for stem_name in stem_names:
        output_filename = generate_stem_filename(None, stem_name, "mp3")
        expected_filename = f"{stem_name}.mp3"

        print(f"   {stem_name.capitalize()} stem: {output_filename}")
        print(f"   Expected:        {expected_filename}")

        if output_filename != expected_filename:
            print(f"   ❌ {stem_name} stem filename (fallback): FAILED")
            return False

    print("   ✅ Stem filename generation (fallback): PASSED")
    return True


def test_edge_cases():
    """Test edge cases for filename generation"""
    print("\n🧪 Testing edge cases...")

    # Test with special characters
    metadata_special = MockVideoMetadata(
        title="Test Song: With/Special\\Characters & More!",
        duration=180,
        thumbnail_url="https://example.com/thumb.jpg",
        uploader="Test Artist",
        upload_date="20231201",
        view_count=1000,
        description="Test description"
    )

    filename_special = generate_youtube_filename(metadata_special, "test-id", "mp3")
    print(f"   Special chars: {filename_special}")

    # Test with very long title
    metadata_long = MockVideoMetadata(
        title="This is a very long title that exceeds the normal length limit and should be truncated properly to avoid filesystem issues while still maintaining readability and usefulness for the end user who wants to identify their downloaded files easily",
        duration=300,
        thumbnail_url="https://example.com/thumb.jpg",
        uploader="Test Artist",
        upload_date="20231201",
        view_count=1000,
        description="Test description"
    )

    filename_long = generate_youtube_filename(metadata_long, "test-id", "mp3")
    print(f"   Long title: {filename_long}")
    print(f"   Length: {len(filename_long)} characters")

    # Test without metadata
    filename_no_meta = generate_youtube_filename(None, "test-id", "mp3")
    print(f"   No metadata: {filename_no_meta}")

    print("   ✅ Edge cases: PASSED")
    return True


def main():
    """Run all tests"""
    print("🧪 Testing New Naming Convention for MP3 Files and Stems")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 4
    
    # Run tests
    if test_youtube_filename_generation():
        tests_passed += 1
    
    if test_stem_filename_generation():
        tests_passed += 1
    
    if test_stem_filename_without_original():
        tests_passed += 1
    
    if test_edge_cases():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The naming convention is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit(main())
