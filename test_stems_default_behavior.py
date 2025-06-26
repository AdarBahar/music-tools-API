#!/usr/bin/env python3
"""
Test script to verify that the stems parameter defaults to all stems when empty or null.
"""

from typing import Optional, List


def parse_stems_parameter(stems: Optional[str]) -> Optional[List[str]]:
    """
    Mock implementation of the stems parameter parsing logic from the API
    """
    requested_stems = None
    valid_stems = ['vocals', 'drums', 'bass', 'other']
    
    if stems and stems.strip():  # Check for non-empty string
        requested_stems = [s.strip() for s in stems.split(',') if s.strip()]
        for stem in requested_stems:
            if stem not in valid_stems:
                raise ValueError(f"Invalid stem '{stem}'. Valid stems: {valid_stems}")
    
    # If stems is None, empty string, or only whitespace, requested_stems remains None
    # This will default to all stems in the service layer
    return requested_stems


def process_stems_with_default(requested_stems: Optional[List[str]]) -> List[str]:
    """
    Mock implementation of the service layer logic that defaults to all stems
    """
    available_stems = ['vocals', 'drums', 'bass', 'other']
    
    # Process requested stems (or all if none specified)
    stems_to_process = requested_stems if requested_stems else available_stems
    
    return stems_to_process


def test_stems_parameter_behavior():
    """Test various inputs for the stems parameter"""
    print("🧪 Testing stems parameter default behavior...")
    
    test_cases = [
        # (input, expected_parsed, expected_processed, description)
        (None, None, ['vocals', 'drums', 'bass', 'other'], "None input"),
        ("", None, ['vocals', 'drums', 'bass', 'other'], "Empty string"),
        ("   ", None, ['vocals', 'drums', 'bass', 'other'], "Whitespace only"),
        ("vocals", ['vocals'], ['vocals'], "Single stem"),
        ("vocals,drums", ['vocals', 'drums'], ['vocals', 'drums'], "Multiple stems"),
        ("vocals, drums, bass", ['vocals', 'drums', 'bass'], ['vocals', 'drums', 'bass'], "Multiple stems with spaces"),
        ("vocals,drums,bass,other", ['vocals', 'drums', 'bass', 'other'], ['vocals', 'drums', 'bass', 'other'], "All stems explicitly"),
        ("vocals,,drums", ['vocals', 'drums'], ['vocals', 'drums'], "Empty values in list"),
        (" vocals , drums ", ['vocals', 'drums'], ['vocals', 'drums'], "Stems with extra whitespace"),
    ]
    
    all_passed = True
    
    for i, (input_value, expected_parsed, expected_processed, description) in enumerate(test_cases, 1):
        try:
            # Test parsing
            parsed = parse_stems_parameter(input_value)
            
            # Test processing with default
            processed = process_stems_with_default(parsed)
            
            # Check results
            if parsed == expected_parsed and processed == expected_processed:
                print(f"   ✅ Test {i}: {description}")
                print(f"      Input: {repr(input_value)}")
                print(f"      Parsed: {parsed}")
                print(f"      Processed: {processed}")
            else:
                print(f"   ❌ Test {i}: {description} - FAILED")
                print(f"      Input: {repr(input_value)}")
                print(f"      Expected parsed: {expected_parsed}, got: {parsed}")
                print(f"      Expected processed: {expected_processed}, got: {processed}")
                all_passed = False
                
        except Exception as e:
            print(f"   ❌ Test {i}: {description} - ERROR: {e}")
            all_passed = False
        
        print()
    
    return all_passed


def test_invalid_stems():
    """Test invalid stem values"""
    print("🧪 Testing invalid stem values...")
    
    invalid_cases = [
        "invalid_stem",
        "vocals,invalid",
        "guitar,piano",
        "vocals,drums,invalid_stem"
    ]
    
    all_passed = True
    
    for i, invalid_input in enumerate(invalid_cases, 1):
        try:
            parse_stems_parameter(invalid_input)
            print(f"   ❌ Test {i}: Should have failed for '{invalid_input}'")
            all_passed = False
        except ValueError as e:
            print(f"   ✅ Test {i}: Correctly rejected '{invalid_input}' - {e}")
        except Exception as e:
            print(f"   ❌ Test {i}: Unexpected error for '{invalid_input}' - {e}")
            all_passed = False
    
    return all_passed


def main():
    """Run all tests"""
    print("🎛️ Testing Stems Parameter Default Behavior")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 2
    
    # Run tests
    if test_stems_parameter_behavior():
        tests_passed += 1
    
    print()
    if test_invalid_stems():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tests_passed}/{total_tests} test suites passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The stems parameter correctly defaults to all stems when empty or null.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit(main())
