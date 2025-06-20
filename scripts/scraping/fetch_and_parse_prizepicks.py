#!/usr/bin/env python3
"""
Fetch AND properly parse PrizePicks WNBA props
Combines fetching with correct parsing logic
"""

import httpx
import json
import csv
from datetime import datetime
from pathlib import Path

def fetch_and_parse_prizepicks():
    """Fetch fresh PrizePicks data and parse it correctly"""
    
    print("📡 Fetching PrizePicks WNBA data...")
    
    # API endpoint
    url = "https://api.prizepicks.com/projections"
    
    # Headers to avoid detection
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://app.prizepicks.com/',
        'Origin': 'https://app.prizepicks.com'
    }
    
    try:
        # Fetch data
        with httpx.Client() as client:
            response = client.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Failed to fetch: HTTP {response.status_code}")
                return False
            
            raw_data = response.json()
            print("✅ Data fetched successfully")
            
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return False
    
    # Parse the data
    print("\n📊 Parsing PrizePicks data...")
    
    projections = raw_data.get('data', [])
    included = raw_data.get('included', [])
    
    print(f"Total projections: {len(projections)}")
    print(f"Total included items: {len(included)}")
    
    # Build player lookup
    players = {}
    for item in included:
        if item.get('type') == 'new_player':
            players[item['id']] = item.get('attributes', {})
    
    print(f"Found {len(players)} players")
    
    # Parse WNBA props
    wnba_props = []
    
    for proj in projections:
        attrs = proj.get('attributes', {})
        relationships = proj.get('relationships', {})
        
        # Get player info
        player_rel = relationships.get('new_player', {}).get('data', {})
        player_id = player_rel.get('id')
        player_info = players.get(player_id, {})
        
        # Only keep WNBA props
        if player_info.get('league') == 'WNBA':
            prop = {
                'player_name': player_info.get('name', 'Unknown'),
                'team_name': player_info.get('team', 'Unknown'),
                'stat_type': attrs.get('stat_type', 'Unknown'),
                'line': float(attrs.get('line_score', 0)),
                'timestamp': datetime.now().isoformat()
            }
            wnba_props.append(prop)
    
    print(f"\n🏀 Found {len(wnba_props)} WNBA props")
    
    # Save the data
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    if wnba_props:
        # Show sample
        print("\n📋 Sample WNBA Props:")
        print("-" * 60)
        for i, prop in enumerate(wnba_props[:10]):
            print(f"{i+1:2d}. {prop['player_name']:<25} {prop['stat_type']:<20} {prop['line']:>6.1f}")
        
        # Save to CSV
        csv_path = data_dir / "wnba_prizepicks_props.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['player_name', 'team_name', 'stat_type', 'line', 'timestamp'])
            writer.writeheader()
            writer.writerows(wnba_props)
        
        # Save to JSON
        json_path = data_dir / "wnba_prizepicks_props.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(wnba_props, f, indent=2)
        
        print(f"\n✅ Saved {len(wnba_props)} WNBA props to:")
        print(f"  - {csv_path}")
        print(f"  - {json_path}")
        
        # Also save raw data for backup
        raw_path = data_dir / "raw" / "wnba_prizepicks_raw.json"
        raw_path.parent.mkdir(exist_ok=True)
        with open(raw_path, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=2)
        print(f"\n📦 Raw data saved to: {raw_path}")
        
    else:
        print("\n⚠️ No WNBA props found!")
        print("Possible reasons:")
        print("  - No WNBA games scheduled today")
        print("  - API returned data for other sports only")
        print("  - Data structure has changed")
        
        # Save raw data anyway for debugging
        raw_path = data_dir / "raw" / "debug_prizepicks_raw.json"
        raw_path.parent.mkdir(exist_ok=True)
        with open(raw_path, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=2)
        print(f"\n📦 Raw data saved for debugging: {raw_path}")
        
        # Show what leagues are available
        league_counts = {}
        for player in players.values():
            league = player.get('league', 'Unknown')
            league_counts[league] = league_counts.get(league, 0) + 1
        
        if league_counts:
            print("\n📊 Available leagues in data:")
            for league, count in sorted(league_counts.items()):
                print(f"  {league}: {count} players")
    
    return True


if __name__ == "__main__":
    fetch_and_parse_prizepicks()