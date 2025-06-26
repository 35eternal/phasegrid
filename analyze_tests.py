import os
import ast
import json
from pathlib import Path

def analyze_tests():
    """Analyze test files for xfailed, skipped, and regular tests."""
    
    test_dir = Path("tests")
    stats = {
        "total_test_files": 0,
        "total_tests": 0,
        "xfailed_tests": [],
        "skipped_tests": [],
        "regular_tests": 0
    }
    
    # Scan all test files
    for test_file in test_dir.glob("test_*.py"):
        stats["total_test_files"] += 1
        
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Count test functions
        test_count = content.count("def test_")
        stats["total_tests"] += test_count
        
        # Find xfailed tests
        if "@pytest.mark.xfail" in content:
            xfail_count = content.count("@pytest.mark.xfail")
            stats["xfailed_tests"].append({
                "file": test_file.name,
                "count": xfail_count
            })
            
        # Find skipped tests  
        if "@pytest.mark.skip" in content:
            skip_count = content.count("@pytest.mark.skip")
            stats["skipped_tests"].append({
                "file": test_file.name,
                "count": skip_count
            })
    
    # Calculate regular tests
    total_marked = sum(x["count"] for x in stats["xfailed_tests"]) + sum(x["count"] for x in stats["skipped_tests"])
    stats["regular_tests"] = stats["total_tests"] - total_marked
    
    # Print report
    print("🧪 TEST ANALYSIS REPORT 🧪")
    print("=" * 50)
    print(f"Total test files: {stats['total_test_files']}")
    print(f"Total test functions: {stats['total_tests']}")
    print(f"Regular tests: {stats['regular_tests']}")
    print(f"\nXFailed tests: {sum(x['count'] for x in stats['xfailed_tests'])}")
    for xfail in stats["xfailed_tests"]:
        print(f"  - {xfail['file']}: {xfail['count']} xfailed")
    print(f"\nSkipped tests: {sum(x['count'] for x in stats['skipped_tests'])}")
    for skip in stats["skipped_tests"]:
        print(f"  - {skip['file']}: {skip['count']} skipped")
    
    # Save to JSON
    with open("test_analysis.json", "w") as f:
        json.dump(stats, f, indent=2)
    print(f"\n✅ Saved detailed analysis to test_analysis.json")

if __name__ == "__main__":
    analyze_tests()
