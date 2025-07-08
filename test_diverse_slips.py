import json
from slip_optimizer import build_slips
from phasegrid.errors import InsufficientSlipsError

# Load diverse data
with open("data/wnba_diverse_props.json", "r") as f:
    diverse_props = json.load(f)

print(f"Testing with {len(diverse_props)} diverse props across multiple games")

# Transform data
transformed = []
for prop in diverse_props:
    # Over version
    transformed.append({
        'player': prop['player'],
        'team': prop['team'], 
        'prop_type': prop['prop_type'],
        'line': prop['line'],
        'over_under': 'over',
        'odds': prop['over_odds'],
        'confidence': prop['confidence'],
        'game': prop['game']
    })
    
    # Under version
    transformed.append({
        'player': prop['player'],
        'team': prop['team'],
        'prop_type': prop['prop_type'], 
        'line': prop['line'],
        'over_under': 'under',
        'odds': prop['under_odds'],
        'confidence': max(0.45, prop['confidence'] - 0.05),
        'game': prop['game']
    })

print(f"Transformed to {len(transformed)} bets")

# Test with different target counts
for target in [5, 10, 15]:
    print(f"\n--- Testing with target_count={target} ---")
    try:
        slips = build_slips(transformed, target_count=target)
        print(f"✅ Generated {len(slips)} slips")
        
        # Analyze slip composition
        power_slips = [s for s in slips if s.slip_type == 'Power']
        flex_slips = [s for s in slips if s.slip_type == 'Flex']
        
        print(f"   Power: {len(power_slips)}, Flex: {len(flex_slips)}")
        print(f"   EV range: {min(s.expected_value for s in slips):.3f} to {max(s.expected_value for s in slips):.3f}")
        
    except InsufficientSlipsError as e:
        print(f"❌ {e}")
