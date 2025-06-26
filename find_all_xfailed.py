import re
from pathlib import Path

def find_all_xfailed_tests():
    """Find ALL xfailed tests including those marked inline."""
    test_dir = Path("tests")
    xfailed_tests = []
    
    for test_file in test_dir.glob("test_*.py"):
        with open(test_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            # Look for various xfail patterns
            if 'xfail' in line.lower():
                # Get surrounding context
                start = max(0, i-2)
                end = min(len(lines), i+3)
                context = ''.join(lines[start:end])
                
                # Try to find test name
                test_match = re.search(r'def (test_\w+)', context)
                test_name = test_match.group(1) if test_match else f"Line {i+1}"
                
                xfailed_tests.append({
                    'file': test_file.name,
                    'line': i + 1,
                    'test': test_name,
                    'context': line.strip()
                })
    
    # Print detailed report
    print("❌ COMPREHENSIVE XFAILED TESTS REPORT ❌")
    print("=" * 80)
    print(f"Total xfailed references: {len(xfailed_tests)}")
    print()
    
    # Group by file
    by_file = {}
    for test in xfailed_tests:
        if test['file'] not in by_file:
            by_file[test['file']] = []
        by_file[test['file']].append(test)
    
    for file, tests in sorted(by_file.items()):
        print(f"\n📄 {file} ({len(tests)} xfail references):")
        for test in tests[:5]:  # Show first 5
            print(f"  Line {test['line']}: {test['test']}")
            print(f"    Context: {test['context'][:80]}...")
        if len(tests) > 5:
            print(f"  ... and {len(tests) - 5} more")

if __name__ == "__main__":
    find_all_xfailed_tests()
