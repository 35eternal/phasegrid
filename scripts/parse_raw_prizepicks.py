#!/usr/bin/env python3
"""
Parse the raw PrizePicks JSON data correctly
"""

import json
import csv
from pathlib import Path
from datetime import datetime

# Get project root
project_root = Path(__file__).parent.parent.parent
data_dir = project_root / "data"
raw_file = data_dir / "raw" / "wnba_prizepicks_props.json"

print("🏀 Parsing Raw PrizePicks Data")
print("=" * 50)

if not raw_file.exists():
    print(f"❌ Raw file not found: {raw_file}")
    exit(1)

# Load the raw data
with open(raw_file, 'r') as f:
    raw_data = json.load(f)

print(f"✅ Loaded raw data with keys: {list(raw_data.keys())}")

# PrizePicks API structure:
# - data: contains the projections
# - included: contains player and game information

projections = raw_data.get('data', [])
included = raw_data.get('included', [])

print(f"\n📊 Found {len(projections)} projections")
print(f"📊 Found {len(included)} included items")

# Build lookup dictionaries
players = {}
games = {}

for item in included:
    if item.get('type') == 'new_player':
        players[item['id']] = item['attributes']
    elif item.get('type') == 'game':
        games[item['id']] = item['attributes']

print(f"\n👥 Found {len(players)} players")
print(f"🏟️ Found {len(games)} games")

# Parse projections
parsed_props = []
wnba_props = []

for proj in projections:
    attrs = proj.get('attributes', {})
    relationships = proj.get('relationships', {})
    
    # Get player info
    player_rel = relationships.get('new_player', {}).get('data', {})
    player_id = player_rel.get('id')
    player_info = players.get(player_id, {})
    
    # Get game info
    game_rel = relationships.get('game', {}).get('data', {})
    game_id = game_rel.get('id')
    game_info = games.get(game_id, {})
    
    # Create prop entry
    prop = {
        'player_name': player_info.get('name', 'Unknown'),
        'team_name': player_info.get('team', 'Unknown'),
        'stat_type': attrs.get('stat_type', 'Unknown'),
        'line': float(attrs.get('line_score', 0)),
        'league': player_info.get('league', game_info.get('league', 'Unknown')),
        'game_id': game_id,
        'start_time': attrs.get('start_time', ''),
        'timestamp': datetime.now().isoformat()
    }
    
    parsed_props.append(prop)
    
    # Filter for WNBA
    if prop['league'] == 'WNBA':
        wnba_prop = {
            'player_name': prop['player_name'],
            'team_name': prop['team_name'],
            'stat_type': prop['stat_type'],
            'line': prop['line'],
            'timestamp': prop['timestamp']
        }
        wnba_props.append(wnba_prop)

print(f"\n✅ Parsed {len(parsed_props)} total props")
print(f"🏀 Found {len(wnba_props)} WNBA props")

# Show sample WNBA props
if wnba_props:
    print("\n📋 Sample WNBA Props:")
    print("-" * 60)
    for i, prop in enumerate(wnba_props[:10]):
        print(f"{i+1:2d}. {prop['player_name']:<25} {prop['stat_type']:<20} {prop['line']:>6.1f}")

# Save corrected WNBA data
if wnba_props:
    # JSON
    json_path = data_dir / "wnba_prizepicks_props_fixed.json"
    with open(json_path, 'w') as f:
        json.dump(wnba_props, f, indent=2)
    
    # CSV
    csv_path = data_dir / "wnba_prizepicks_props_fixed.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['player_name', 'team_name', 'stat_type', 'line', 'timestamp'])
        writer.writeheader()
        writer.writerows(wnba_props)
    
    print(f"\n✅ Saved corrected data:")
    print(f"  - {json_path}")
    print(f"  - {csv_path}")
    
    # Also overwrite the bad files
    json_path_main = data_dir / "wnba_prizepicks_props.json"
    csv_path_main = data_dir / "wnba_prizepicks_props.csv"
    
    with open(json_path_main, 'w') as f:
        json.dump(wnba_props, f, indent=2)
    
    with open(csv_path_main, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['player_name', 'team_name', 'stat_type', 'line', 'timestamp'])
        writer.writeheader()
        writer.writerows(wnba_props)
    
    print(f"\n✅ Updated main files:")
    print(f"  - {json_path_main}")
    print(f"  - {csv_path_main}")
    
else:
    print("\n⚠️ No WNBA props found in the data")
    print("This might mean no WNBA games are scheduled")
    
    # Show what leagues are available
    leagues = set(prop['league'] for prop in parsed_props)
    print(f"\nAvailable leagues: {leagues}")

# Show stats
print(f"\n📊 Stats by league:")
league_counts = {}
for prop in parsed_props:
    league = prop['league']
    league_counts[league] = league_counts.get(league, 0) + 1

for league, count in sorted(league_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  - {league}: {count} props")