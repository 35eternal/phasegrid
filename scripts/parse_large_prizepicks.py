#!/usr/bin/env python3
"""
Parse the large 10MB prizepicks_props.json file
"""

import json
import csv
from datetime import datetime

print("🏀 Parsing Large PrizePicks Data File")
print("=" * 50)

# The 10MB file from 6/3/2025
input_file = "data/prizepicks_props.json"

try:
    print(f"Loading {input_file} (10MB)...")
    with open(input_file, 'r') as f:
        raw_data = json.load(f)
    print("✅ Loaded successfully")
except Exception as e:
    print(f"❌ Error loading file: {e}")
    exit(1)

# Parse based on structure
if isinstance(raw_data, dict) and 'data' in raw_data:
    print("\n📊 Parsing PrizePicks API data...")
    
    projections = raw_data.get('data', [])
    included = raw_data.get('included', [])
    
    print(f"Total projections: {len(projections)}")
    print(f"Total included items: {len(included)}")
    
    # Build lookups
    players = {}
    games = {}
    
    for item in included:
        item_type = item.get('type')
        item_id = item.get('id')
        
        if item_type == 'new_player':
            players[item_id] = item.get('attributes', {})
        elif item_type == 'game':
            games[item_id] = item.get('attributes', {})
    
    print(f"\nFound {len(players)} players")
    print(f"Found {len(games)} games")
    
    # Count leagues
    league_counts = {}
    for player in players.values():
        league = player.get('league', 'Unknown')
        league_counts[league] = league_counts.get(league, 0) + 1
    
    print("\nPlayers by league:")
    for league, count in sorted(league_counts.items()):
        print(f"  {league}: {count}")
    
    # Parse WNBA props
    wnba_props = []
    all_props = []
    
    for proj in projections:
        proj_id = proj.get('id')
        attrs = proj.get('attributes', {})
        relationships = proj.get('relationships', {})
        
        # Get player
        player_rel = relationships.get('new_player', {}).get('data', {})
        player_id = player_rel.get('id')
        player_info = players.get(player_id, {})
        
        # Get game
        game_rel = relationships.get('game', {}).get('data', {})
        game_id = game_rel.get('id')
        game_info = games.get(game_id, {})
        
        prop = {
            'player_name': player_info.get('name', 'Unknown'),
            'team_name': player_info.get('team', 'Unknown'),
            'stat_type': attrs.get('stat_type', 'Unknown'),
            'line': float(attrs.get('line_score', 0)),
            'league': player_info.get('league', 'Unknown'),
            'position': player_info.get('position', ''),
            'game_id': game_id,
            'start_time': attrs.get('start_time', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        all_props.append(prop)
        
        # Filter WNBA
        if player_info.get('league') == 'WNBA':
            wnba_prop = {
                'player_name': prop['player_name'],
                'team_name': prop['team_name'],
                'stat_type': prop['stat_type'],
                'line': prop['line'],
                'timestamp': prop['timestamp']
            }
            wnba_props.append(wnba_prop)
    
    print(f"\n✅ Parsed {len(all_props)} total props")
    print(f"🏀 Found {len(wnba_props)} WNBA props")
    
    # Show WNBA sample
    if wnba_props:
        print("\n📋 Sample WNBA Props:")
        print("-" * 70)
        print(f"{'Player':<25} {'Team':<15} {'Stat':<20} {'Line':>6}")
        print("-" * 70)
        
        for prop in wnba_props[:15]:
            print(f"{prop['player_name']:<25} {prop['team_name']:<15} {prop['stat_type']:<20} {prop['line']:>6.1f}")
        
        # Save WNBA props
        csv_path = "data/wnba_prizepicks_props_parsed.csv"
        json_path = "data/wnba_prizepicks_props_parsed.json"
        
        # CSV
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['player_name', 'team_name', 'stat_type', 'line', 'timestamp'])
            writer.writeheader()
            writer.writerows(wnba_props)
        
        # JSON
        with open(json_path, 'w') as f:
            json.dump(wnba_props, f, indent=2)
        
        print(f"\n✅ Saved {len(wnba_props)} WNBA props to:")
        print(f"  - {csv_path}")
        print(f"  - {json_path}")
        
        # Also save all props for reference
        all_csv = "data/all_prizepicks_props.csv"
        with open(all_csv, 'w', newline='') as f:
            all_fields = ['player_name', 'team_name', 'stat_type', 'line', 'league', 'position', 'timestamp']
            writer = csv.DictWriter(f, fieldnames=all_fields)
            writer.writeheader()
            for prop in all_props:
                writer.writerow({k: prop.get(k, '') for k in all_fields})
        
        print(f"\n📊 Also saved all {len(all_props)} props (all leagues) to:")
        print(f"  - {all_csv}")
        
    else:
        print("\n⚠️ No WNBA props found")
        print("This data might be from a time when no WNBA games were scheduled")
        
        # Show what's available
        print("\n📊 Props by league:")
        league_summary = {}
        for prop in all_props:
            league = prop['league']
            league_summary[league] = league_summary.get(league, 0) + 1
        
        for league, count in sorted(league_summary.items(), key=lambda x: x[1], reverse=True):
            print(f"  {league}: {count} props")

else:
    print("\n❌ Unexpected data structure")
    print(f"Type: {type(raw_data)}")
    if isinstance(raw_data, dict):
        print(f"Keys: {list(raw_data.keys())[:20]}")