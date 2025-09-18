#!/usr/bin/env python3
"""
Simple test script for LRU implementation only
"""

import subprocess
import sys
import os

def test_lru(trace_file, frames, expected_file=None):
    """Test LRU algorithm with a specific trace and frame count"""
    print(f"\n=== Testing {trace_file} with {frames} frames using LRU ===")
    
    try:
        # Run the simulator with LRU
        result = subprocess.run([
            sys.executable, 'memsim.py', 
            trace_file, str(frames), 'lru', 'quiet'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"ERROR: {result.stderr}")
            return False
            
        output = result.stdout.strip()
        print("Your output:")
        print(output)
        
        # Compare with expected if provided
        if expected_file and os.path.exists(expected_file):
            with open(expected_file, 'r') as f:
                expected = f.read().strip()
            
            print(f"\nExpected output:")
            print(expected)
            
            if output == expected:
                print("✅ PASS: Output matches expected!")
                return True
            else:
                print("❌ FAIL: Output doesn't match")
                
                # Show detailed comparison
                output_lines = output.split('\n')
                expected_lines = expected.split('\n')
                
                print("\nDetailed comparison:")
                for i, (actual, expect) in enumerate(zip(output_lines, expected_lines)):
                    if actual != expect:
                        print(f"  Line {i+1}: Got '{actual}' | Expected '{expect}'")
                return False
        else:
            print("⚠️  No expected output file to compare")
            return True
            
    except subprocess.TimeoutExpired:
        print("❌ FAIL: Test timed out!")
        return False
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {e}")
        return False

def test_with_debug(trace_file, frames):
    """Run a test with debug output to see what's happening"""
    print(f"\n=== Debug run: {trace_file} with {frames} frames ===")
    
    try:
        result = subprocess.run([
            sys.executable, 'memsim.py', 
            trace_file, str(frames), 'lru', 'debug'
        ], capture_output=True, text=True, timeout=30)
        
        print("Debug output:")
        print(result.stdout)
        
        if result.stderr:
            print("Errors:")
            print(result.stderr)
            
    except Exception as e:
        print(f"Debug run failed: {e}")

def main():
    print("LRU Page Replacement Algorithm Tester")
    print("=" * 50)
    
    # Test cases for LRU only
    lru_tests = [
        ('trace1', 4, 'trace1-4frames-lru'),
        ('trace1', 8, 'trace1-8frames-lru'),
        ('trace2', 6, 'trace2-6frames-lru.ans'),
        ('trace3', 4, 'trace3-4frames-lru'),
    ]
    
    passed = 0
    total = 0
    
    # Run all LRU tests
    for trace_file, frames, expected_file in lru_tests:
        if os.path.exists(trace_file):
            total += 1
            if test_lru(trace_file, frames, expected_file):
                passed += 1
        else:
            print(f"⚠️  Skipping {trace_file} - file not found")
    
    print(f"\n=== LRU Test Summary ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total and total > 0:
        print("🎉 All LRU tests passed!")
    elif passed > 0:
        print("⚠️  Some LRU tests failed")
        
        # Offer to run debug mode for failed test
        print("\nWould you like to see debug output for trace1 with 4 frames? (y/n)")
        if input().lower().startswith('y'):
            test_with_debug('trace1', 4)
    else:
        print("❌ All LRU tests failed")
        print("\nRunning debug output for trace1 to help diagnose:")
        test_with_debug('trace1', 4)

if __name__ == "__main__":
    main()