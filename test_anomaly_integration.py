"""
Integration test for anomaly filter in the auto_paper pipeline.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phasegrid.anomaly_filter import AnomalyFilter

def test_integration():
    """Test that anomaly filter integrates properly with board data."""
    
    # Sample board data with demons/goblins
    board = [
        {'player': 'A. Wilson', 'prop_type': 'points', 'line': 18.5, 'odds': -110},  # Goblin
        {'player': 'A. Wilson', 'prop_type': 'points', 'line': 22.5, 'odds': -110},  # Standard
        {'player': 'A. Wilson', 'prop_type': 'points', 'line': 26.5, 'odds': -110},  # Demon
        {'player': 'B. Stewart', 'prop_type': 'rebounds', 'line': 8.5, 'odds': -110},
    ]
    
    # Apply filter
    filter = AnomalyFilter()
    filtered = filter.filter_anomalies(board)
    
    # Verify results
    assert len(filtered) == 2, f"Expected 2 props, got {len(filtered)}"
    
    # Check A. Wilson has only standard line
    wilson_props = [p for p in filtered if p['player'] == 'A. Wilson']
    assert len(wilson_props) == 1
    assert wilson_props[0]['line'] == 22.5
    
    print("✅ Integration test passed!")
    print(f"Filtered {len(board)} props down to {len(filtered)} standard props")
    
if __name__ == "__main__":
    test_integration()
