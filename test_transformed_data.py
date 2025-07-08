import json
from slip_optimizer import build_slips
from phasegrid.errors import InsufficientSlipsError

# Load test data
with open("data/wnba_test_props.json", "r") as f:
    test_props = json.load(f)

print(f"Transforming {len(test_props)} props...")

# Transform data to match SlipOptimizer expectations
transformed_props = []
for prop in test_props:
    # For each prop, create both over and under versions
    # Over version
    over_prop = {
        'player': prop['player'],
        'team': prop['team'],
        'prop_type': prop['prop_type'],
        'line': prop['line'],
        'over_under': 'over',
        'odds': prop['over_odds'],
        'confidence': prop['confidence'],
        'game': prop['game']
    }
    transformed_props.append(over_prop)
    
    # Under version (with slightly adjusted confidence)
    under_prop = {
        'player': prop['player'],
        'team': prop['team'],
        'prop_type': prop['prop_type'],
        'line': prop['line'],
        'over_under': 'under',
        'odds': prop['under_odds'],
        'confidence': max(0.45, prop['confidence'] - 0.1),  # Slightly lower confidence for under
        'game': prop['game']
    }
    transformed_props.append(under_prop)

print(f"Transformed to {len(transformed_props)} bets (over/under for each prop)")

# Now test slip generation
try:
    slips = build_slips(transformed_props, target_count=10)
    print(f"\n✅ Generated {len(slips)} slips successfully!")
    
    # Show slip details
    for i, slip in enumerate(slips[:3]):
        print(f"\nSlip {i+1}:")
        print(f"  Type: {slip.slip_type}")
        print(f"  Legs: {len(slip.bets)}")
        print(f"  Expected Value: {slip.expected_value:.4f}")
        print(f"  Total Odds: {slip.total_odds:.2f}")
        print(f"  Confidence: {slip.confidence:.4f}")
        
except InsufficientSlipsError as e:
    print(f"\n❌ InsufficientSlipsError: {e}")
    print("Trying with bypass_guard_rail=True...")
    
    slips = build_slips(transformed_props, target_count=10, bypass_guard_rail=True)
    print(f"Generated {len(slips)} slips with bypass")
    
    for i, slip in enumerate(slips):
        print(f"  Slip {i+1}: {slip.slip_type} ({len(slip.bets)} legs) - EV: {slip.expected_value:.4f}")
