import re
from pathlib import Path

def find_xfailed_tests():
    """Find all xfailed tests and their reasons."""
    test_dir = Path("tests")
    xfailed_tests = []
    
    for test_file in test_dir.glob("test_*.py"):
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find xfail decorators and the following test function
        pattern = r'@pytest\.mark\.xfail\(reason="([^"]+)"\)\s*\n\s*def (test_\w+)'
        matches = re.findall(pattern, content)
        
        for reason, test_name in matches:
            xfailed_tests.append({
                'file': test_file.name,
                'test': test_name,
                'reason': reason
            })
    
    # Print report
    print("❌ XFAILED TESTS REPORT ❌")
    print("=" * 80)
    print(f"Total xfailed tests: {len(xfailed_tests)}")
    print()
    
    # Group by file
    by_file = {}
    for test in xfailed_tests:
        if test['file'] not in by_file:
            by_file[test['file']] = []
        by_file[test['file']].append(test)
    
    for file, tests in by_file.items():
        print(f"\n📄 {file}:")
        for test in tests:
            print(f"  - {test['test']}")
            print(f"    Reason: {test['reason']}")

if __name__ == "__main__":
    find_xfailed_tests()
