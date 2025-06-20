#!/usr/bin/env python3
"""Run all tests with coverage report."""

import pytest
import sys
from pathlib import Path

def main():
    """Run test suite with coverage."""
    # Add project root to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Test arguments
    args = [
        # Test files
        'tests/',
        
        # Verbosity
        '-v',
        
        # Coverage
        '--cov=.',
        '--cov-config=.coveragerc',
        '--cov-report=term-missing',
        '--cov-report=html:output/coverage_html',
        
        # Exclude patterns from coverage
        '--cov-omit=*/tests/*,*/test_*,setup.py,run_tests.py,*/migrations/*,*/__pycache__/*',
        
        # Other options
        '--tb=short',
        '-x',  # Stop on first failure
        
        # Capture output
        '-s'
    ]
    
    # Add any command line arguments
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])
    
    print("="*60)
    print("Running PhaseGrid Test Suite")
    print("="*60)
    
    # Run pytest
    exit_code = pytest.main(args)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
        
        # Check coverage threshold
        try:
            import coverage
            cov = coverage.Coverage()
            cov.load()
            total_coverage = cov.report()
            
            if total_coverage >= 90:
                print(f"✅ Coverage target met: {total_coverage:.1f}% (target: 90%)")
            else:
                print(f"⚠️  Coverage below target: {total_coverage:.1f}% (target: 90%)")
                
        except:
            pass
            
    else:
        print("\n❌ Tests failed!")
        
    return exit_code

if __name__ == "__main__":
    sys.exit(main())