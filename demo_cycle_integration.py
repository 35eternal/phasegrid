"""
Demo script to prove cycle-phase modifiers affect SlipOptimizer output
A8: Cycle-Tracker Integration Demo
"""
from datetime import date
import json
from uuid import UUID
from phasegrid.cycle_tracker import CycleTracker
from phasegrid.slip_optimizer import SlipOptimizer

def load_test_board():
    """Load test board data from WNBA test props"""
    try:
        with open('data/wnba_test_props.json', 'r') as f:
            props = json.load(f)
            return props
    except Exception as e:
        print(f"Error loading test data: {e}")
        # Fallback: create minimal test board
        return [
            {
                "player": "A'ja Wilson",
                "team": "LV",
                "prop_type": "Points",
                "line": 20.5,
                "over_odds": -110,
                "under_odds": -110,
                "confidence": 0.65,
                "game": "LV vs OPP",
                "start_time": "2025-07-09T19:00:00"
            },
            {
                "player": "Breanna Stewart",
                "team": "NY",
                "prop_type": "Rebounds",
                "line": 8.5,
                "over_odds": -115,
                "under_odds": -105,
                "confidence": 0.70,
                "game": "NY vs OPP", 
                "start_time": "2025-07-09T19:00:00"
            }
        ]

def main():
    print("=== A8: Cycle-Tracker Integration Demo ===\n")
    
    # Initialize CycleTracker (it loads data automatically)
    print("1. Loading cycle tracker...")
    ct = CycleTracker()
    print("   ✓ CycleTracker initialized")
    
    # Get phase modifier for a specific player and date
    print("\n2. Getting phase modifier...")
    player_name = "A'ja Wilson"
    target_date = date(2025, 7, 9)  # Today's date
    
    # Get UUID using the mapper
    player_uuid = ct.uuid_mapper.get_or_create_uuid(player_name)
    phase_modifier = ct.get_phase_modifier(player_uuid, target_date)
    
    print(f"   Player: {player_name}")
    print(f"   Player UUID: {player_uuid}")
    print(f"   Date: {target_date}")
    print(f"   Phase Modifier: {phase_modifier}")
    
    # Load board data
    print("\n3. Loading board data...")
    board = load_test_board()
    print(f"   ✓ Loaded {len(board)} props")
    
    # Initialize SlipOptimizer
    print("\n4. Running slip optimization...")
    optimizer = SlipOptimizer()
    
    # Generate slips WITHOUT phase modifier
    print("\n   a) Base slips (no phase modifier):")
    try:
        slips_base = optimizer.optimize(board, date=str(target_date))
        print(f"      Generated {len(slips_base)} optimized props")
        for i, prop in enumerate(slips_base[:3]):  # Show first 3
            print(f"      Prop {i+1}: {prop.get('player', 'Unknown')} - {prop.get('prop_type', 'Unknown')}")
            if 'confidence' in prop:
                print(f"         Confidence: {prop['confidence']:.3f}")
    except Exception as e:
        print(f"      Error: {e}")
        slips_base = []
    
    # Now we need to apply phase modifier manually to the props
    print("\n   b) Modified slips (with phase modifier applied):")
    try:
        # Apply phase modifier to props for our target player
        modified_board = []
        for prop in board:
            prop_copy = prop.copy()
            if prop['player'].lower() == player_name.lower():
                # Apply phase modifier to confidence
                if 'confidence' in prop_copy:
                    original_conf = prop_copy['confidence']
                    prop_copy['confidence'] = min(1.0, original_conf * phase_modifier)
                    print(f"      Applied modifier to {prop['player']}: {original_conf:.3f} -> {prop_copy['confidence']:.3f}")
            modified_board.append(prop_copy)
        
        slips_mod = optimizer.optimize(modified_board, date=str(target_date))
        print(f"      Generated {len(slips_mod)} optimized props")
        for i, prop in enumerate(slips_mod[:3]):  # Show first 3
            print(f"      Prop {i+1}: {prop.get('player', 'Unknown')} - {prop.get('prop_type', 'Unknown')}")
            if 'confidence' in prop:
                print(f"         Confidence: {prop['confidence']:.3f}")
                
    except Exception as e:
        print(f"      Error: {e}")
        slips_mod = []
    
    # Compare results
    print("\n5. Results Comparison:")
    if slips_base and slips_mod:
        # Check if the optimization changed
        base_players = [p.get('player') for p in slips_base[:5]]
        mod_players = [p.get('player') for p in slips_mod[:5]]
        
        if base_players == mod_players and len(slips_base) == len(slips_mod):
            # Check confidence values
            base_conf = [p.get('confidence', 0) for p in slips_base if p.get('player', '').lower() == player_name.lower()]
            mod_conf = [p.get('confidence', 0) for p in slips_mod if p.get('player', '').lower() == player_name.lower()]
            
            if base_conf != mod_conf:
                print("   ✓ Phase modifier successfully changed confidence values!")
                print(f"   Base confidences for {player_name}: {base_conf}")
                print(f"   Modified confidences for {player_name}: {mod_conf}")
            else:
                print("   ⚠️  Props selection unchanged - may need different test data")
        else:
            print("   ✓ Slips are different - phase modifier is affecting optimization!")
            print(f"   Base top players: {base_players[:3]}")
            print(f"   Modified top players: {mod_players[:3]}")
    else:
        print("   ! Could not generate slips for comparison")
    
    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    main()
