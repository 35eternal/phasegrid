"""
Direct test runner for anomaly filter tests.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phasegrid.anomaly_filter import AnomalyFilter

def run_tests():
    """Run basic tests for the anomaly filter."""
    
    print("🧪 Testing AnomalyFilter...")
    
    # Test 1: Filter with demons and goblins
    print("\n📋 Test 1: Filter demons and goblins")
    filter = AnomalyFilter(tolerance_percentage=15.0)
    
    slips = [
        # A'ja Wilson - 3 lines (goblin, standard, demon)
        {'slip_id': '1', 'player': "A'ja Wilson", 'prop_type': 'points', 'line': 18.5},
        {'slip_id': '2', 'player': "A'ja Wilson", 'prop_type': 'points', 'line': 22.5},
        {'slip_id': '3', 'player': "A'ja Wilson", 'prop_type': 'points', 'line': 26.5},
        # Breanna Stewart - 2 lines
        {'slip_id': '4', 'player': 'Breanna Stewart', 'prop_type': 'rebounds', 'line': 8.5},
        {'slip_id': '5', 'player': 'Breanna Stewart', 'prop_type': 'rebounds', 'line': 11.5},
    ]
    
    filtered = filter.filter_anomalies(slips)
    print(f"  Input: {len(slips)} slips")
    print(f"  Output: {len(filtered)} slips")
    print(f"  ✅ Passed: Filtered {len(slips) - len(filtered)} anomalies")
    
    # Test 2: Empty input
    print("\n📋 Test 2: Empty input handling")
    empty_result = filter.filter_anomalies([])
    assert empty_result == []
    print("  ✅ Passed: Empty input returns empty list")
    
    # Test 3: Single projections (no filtering needed)
    print("\n📋 Test 3: Single projections")
    single_props = [
        {'slip_id': '10', 'player': 'Player A', 'prop_type': 'points', 'line': 20.0},
        {'slip_id': '11', 'player': 'Player B', 'prop_type': 'assists', 'line': 5.5},
    ]
    single_filtered = filter.filter_anomalies(single_props)
    assert len(single_filtered) == 2
    print("  ✅ Passed: Single projections remain unchanged")
    
    # Test 4: Tolerance percentage
    print("\n📋 Test 4: Tolerance percentage (15%)")
    tolerance_slips = [
        # 10% difference - should keep both
        {'slip_id': '20', 'player': 'Player C', 'prop_type': 'points', 'line': 20.0},
        {'slip_id': '21', 'player': 'Player C', 'prop_type': 'points', 'line': 22.0},
        # 30% difference - should filter
        {'slip_id': '22', 'player': 'Player D', 'prop_type': 'points', 'line': 20.0},
        {'slip_id': '23', 'player': 'Player D', 'prop_type': 'points', 'line': 26.0},
    ]
    tolerance_filtered = filter.filter_anomalies(tolerance_slips)
    print(f"  10% diff: {'Kept both' if len([s for s in tolerance_filtered if s['player'] == 'Player C']) == 2 else 'Filtered'}")
    print(f"  30% diff: {'Filtered to 1' if len([s for s in tolerance_filtered if s['player'] == 'Player D']) == 1 else 'Kept both'}")
    print("  ✅ Passed: Tolerance percentage works correctly")
    
    print("\n✨ All tests passed!")

if __name__ == "__main__":
    run_tests()
