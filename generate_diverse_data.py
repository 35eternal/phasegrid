import json
import random
from datetime import datetime, timedelta

def generate_diverse_wnba_data(num_games=10, props_per_player=3):
    """Generate diverse WNBA test data with multiple games"""
    
    teams = ["LV", "NY", "CHI", "LA", "SEA", "PHX", "DAL", "MIN", "IND", "ATL", "CON", "WAS"]
    
    # Create matchups
    games = []
    for i in range(0, len(teams)-1, 2):
        games.append((teams[i], teams[i+1]))
    
    # Player pool with realistic stats
    player_pools = {
        "LV": [("A'ja Wilson", {"Points": 22.5, "Rebounds": 9.5, "Assists": 2.5}),
               ("Kelsey Plum", {"Points": 18.5, "Rebounds": 3.5, "Assists": 4.5}),
               ("Chelsea Gray", {"Points": 14.5, "Rebounds": 3.5, "Assists": 6.5})],
        "NY": [("Breanna Stewart", {"Points": 20.5, "Rebounds": 8.5, "Assists": 3.5}),
               ("Sabrina Ionescu", {"Points": 17.5, "Rebounds": 5.5, "Assists": 6.5}),
               ("Jonquel Jones", {"Points": 15.5, "Rebounds": 8.5, "Assists": 2.5})],
        "CHI": [("Kahleah Copper", {"Points": 17.5, "Rebounds": 5.5, "Assists": 2.5}),
                ("Marina Mabrey", {"Points": 14.5, "Rebounds": 3.5, "Assists": 3.5})],
        "LA": [("Nneka Ogwumike", {"Points": 18.5, "Rebounds": 7.5, "Assists": 2.5}),
               ("Jordin Canada", {"Points": 11.5, "Rebounds": 3.5, "Assists": 5.5})],
        "SEA": [("Jewell Loyd", {"Points": 19.5, "Rebounds": 4.5, "Assists": 3.5}),
                ("Ezi Magbegor", {"Points": 12.5, "Rebounds": 7.5, "Assists": 1.5})],
        "PHX": [("Diana Taurasi", {"Points": 16.5, "Rebounds": 3.5, "Assists": 4.5}),
                ("Brittney Griner", {"Points": 19.5, "Rebounds": 8.5, "Assists": 2.5})],
        "DAL": [("Arike Ogunbowale", {"Points": 21.5, "Rebounds": 4.5, "Assists": 3.5}),
                ("Satou Sabally", {"Points": 17.5, "Rebounds": 7.5, "Assists": 3.5})],
        "MIN": [("Napheesa Collier", {"Points": 20.5, "Rebounds": 8.5, "Assists": 3.5})],
        "IND": [("Caitlin Clark", {"Points": 16.5, "Rebounds": 5.5, "Assists": 7.5}),
                ("Aliyah Boston", {"Points": 14.5, "Rebounds": 8.5, "Assists": 2.5})],
        "ATL": [("Rhyne Howard", {"Points": 16.5, "Rebounds": 4.5, "Assists": 3.5})],
        "CON": [("DeWanna Bonner", {"Points": 15.5, "Rebounds": 6.5, "Assists": 3.5})],
        "WAS": [("Elena Delle Donne", {"Points": 17.5, "Rebounds": 6.5, "Assists": 2.5})]
    }
    
    prop_types = ["Points", "Rebounds", "Assists", "3-Pointers Made", "Pts+Rebs+Asts"]
    
    props = []
    
    for home, away in games:
        game_str = f"{away} @ {home}"
        start_time = (datetime.now() + timedelta(hours=random.randint(2, 8))).isoformat()
        
        # Add props for both teams
        for team in [home, away]:
            if team in player_pools:
                for player_name, base_stats in player_pools[team]:
                    for prop_type in random.sample(prop_types, min(3, len(prop_types))):
                        if prop_type in base_stats:
                            base_line = base_stats[prop_type]
                            # Add some variance
                            line = round(base_line + random.uniform(-2, 2), 1)
                        elif prop_type == "3-Pointers Made":
                            line = round(random.uniform(1.5, 3.5), 1)
                        elif prop_type == "Pts+Rebs+Asts":
                            # Calculate from base stats
                            pts = base_stats.get("Points", 15)
                            reb = base_stats.get("Rebounds", 5)
                            ast = base_stats.get("Assists", 3)
                            line = round(pts + reb + ast + random.uniform(-3, 3), 1)
                        else:
                            continue
                        
                        # Higher confidence for star players
                        is_star = "Wilson" in player_name or "Stewart" in player_name or "Clark" in player_name
                        base_conf = 0.65 if is_star else 0.58
                        confidence = round(base_conf + random.uniform(-0.08, 0.12), 4)
                        
                        prop = {
                            "player": player_name,
                            "team": team,
                            "prop_type": prop_type,
                            "line": line,
                            "over_odds": random.choice([-110, -115, -120, -105]),
                            "under_odds": random.choice([-110, -115, -120, -105]),
                            "confidence": confidence,
                            "game": game_str,
                            "start_time": start_time
                        }
                        props.append(prop)
    
    return props

# Generate and save
props = generate_diverse_wnba_data()
with open("data/wnba_diverse_props.json", "w") as f:
    json.dump(props, f, indent=2)

print(f"Generated {len(props)} diverse props")
print(f"\nGames covered:")
games = set(p['game'] for p in props)
for game in sorted(games):
    game_props = [p for p in props if p['game'] == game]
    print(f"  {game}: {len(game_props)} props")
