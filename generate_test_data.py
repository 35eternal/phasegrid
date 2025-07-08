import json
import random
from datetime import datetime, timedelta

def generate_wnba_test_data(num_props=50):
    """Generate realistic WNBA test data"""
    
    # Real WNBA players
    players = [
        ("A'ja Wilson", "LV"), ("Breanna Stewart", "NY"), ("Arike Ogunbowale", "DAL"),
        ("Jewell Loyd", "SEA"), ("Kelsey Plum", "LV"), ("Sabrina Ionescu", "NY"),
        ("Diana Taurasi", "PHX"), ("Brittney Griner", "PHX"), ("Candace Parker", "LV"),
        ("Nneka Ogwumike", "LA"), ("Aliyah Boston", "IND"), ("Caitlin Clark", "IND")
    ]
    
    prop_types = ["Points", "Rebounds", "Assists", "3-Pointers Made", "Pts+Rebs+Asts", "Blocks", "Steals"]
    
    # Lines based on prop type
    lines_by_type = {
        "Points": (12.5, 25.5, 0.5),
        "Rebounds": (4.5, 10.5, 0.5),
        "Assists": (2.5, 7.5, 0.5),
        "3-Pointers Made": (0.5, 3.5, 0.5),
        "Pts+Rebs+Asts": (20.5, 35.5, 1.0),
        "Blocks": (0.5, 2.5, 0.5),
        "Steals": (0.5, 2.5, 0.5)
    }
    
    props = []
    
    for i in range(num_props):
        player, team = random.choice(players)
        prop_type = random.choice(prop_types)
        min_line, max_line, step = lines_by_type[prop_type]
        line = round(random.uniform(min_line, max_line) / step) * step
        
        # Add some variance in odds
        over_odds = random.choice([-110, -115, -120, -105])
        under_odds = random.choice([-110, -115, -120, -105])
        
        # Generate confidence (higher for test data to ensure we get slips)
        confidence = round(random.uniform(0.55, 0.85), 4)
        
        prop = {
            "player": player,
            "team": team,
            "prop_type": prop_type,
            "line": line,
            "over_odds": over_odds,
            "under_odds": under_odds,
            "confidence": confidence,
            "game": f"{team} vs OPP",
            "start_time": (datetime.now() + timedelta(hours=random.randint(1, 6))).isoformat()
        }
        
        props.append(prop)
    
    return props

# Generate and save test data
test_props = generate_wnba_test_data(50)
with open("data/wnba_test_props.json", "w") as f:
    json.dump(test_props, f, indent=2)

print(f"Generated {len(test_props)} test props")
print("\nSample props:")
for prop in test_props[:3]:
    print(f"  {prop['player']} ({prop['team']}) - {prop['prop_type']}: {prop['line']} (conf: {prop['confidence']})")
