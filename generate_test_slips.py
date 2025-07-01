"""Test slip generator for integration testing."""
import json
import os
from datetime import datetime

def generate_test_slips():
    """Generate test slips for integration testing."""
    
    # Create test slips
    slips = []
    for i in range(7):  # Generate 7 slips (more than the 5 minimum)
        slip = {
            "slip_id": f"TEST_{datetime.now().strftime('%Y%m%d')}_{i+1:03d}",
            "player": f"Test Player {i+1}",
            "team": "Test Team",
            "opponent": "Opponent Team",
            "stat_type": ["Points", "Rebounds", "Assists"][i % 3],
            "line": 15.5 + i,
            "over_under": "over" if i % 2 == 0 else "under",
            "confidence": 0.65 + (i * 0.05),
            "projected": 18.5 + i,
            "timestamp": datetime.now().isoformat()
        }
        slips.append(slip)
    
    # Save to file
    filename = f"paper_slips_{datetime.now().strftime('%Y-%m-%d')}.json"
    data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "slips": slips,
        "total": len(slips),
        "source": "test_generator"
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"? Generated {len(slips)} test slips in {filename}")
    return filename

if __name__ == "__main__":
    generate_test_slips()
