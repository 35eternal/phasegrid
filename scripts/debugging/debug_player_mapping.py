#!/usr/bin/env python3
"""
Debug the player ID mapping issue
"""
import json
import pandas as pd

def debug_player_mapping():
    """Debug why player names are showing as Unknown"""
    
    print("🔍 Debugging Player ID Mapping Issue\n")
    
    # 1. Check what player IDs are in projections
    try:
        with open("data/wnba_prizepicks_props.json", 'r') as f:
            props = json.load(f)
        
        projection_player_ids = set()
        for prop in props:
            if prop.get('player_id'):
                projection_player_ids.add(str(prop['player_id']))
        
        print(f"📋 Player IDs from projections ({len(projection_player_ids)}):")
        for pid in sorted(projection_player_ids):
            print(f"  - {pid}")
            
    except Exception as e:
        print(f"❌ Error reading projections: {e}")
        return
    
    # 2. Check what player IDs we have data for
    fetched_player_ids = set()
    sample_fetched_players = {}
    
    for prop in props[:5]:  # Check first 5 props
        pid = str(prop.get('player_id', ''))
        name = prop.get('player_name', 'Unknown')
        team = prop.get('team', '')
        
        fetched_player_ids.add(pid)
        sample_fetched_players[pid] = {
            'name': name,
            'team': team
        }
    
    print(f"\n🔍 Sample player data from enriched props:")
    for pid, info in sample_fetched_players.items():
        print(f"  ID {pid}: {info['name']} ({info['team']})")
    
    # 3. Check for ID overlap
    matching_ids = projection_player_ids.intersection(fetched_player_ids)
    missing_ids = projection_player_ids - fetched_player_ids
    
    print(f"\n📊 ID Analysis:")
    print(f"  Projection IDs: {len(projection_player_ids)}")
    print(f"  Fetched IDs: {len(fetched_player_ids)}")
    print(f"  Matching IDs: {len(matching_ids)}")
    print(f"  Missing IDs: {len(missing_ids)}")
    
    if missing_ids:
        print(f"\n❌ Missing player IDs (in projections but not fetched):")
        for pid in sorted(missing_ids):
            print(f"  - {pid}")
    
    # 4. Test individual player fetch for missing IDs
    if missing_ids:
        print(f"\n🧪 Testing individual fetches for missing IDs...")
        
        import requests
        
        HEADERS = {
            "Accept": "application/json",
            "Origin": "https://app.prizepicks.com",
            "Referer": "https://app.prizepicks.com/",
            "User-Agent": "Mozilla/5.0"
        }
        
        for pid in list(missing_ids)[:3]:  # Test first 3
            try:
                response = requests.get(
                    f"https://api.prizepicks.com/players/{pid}",
                    headers=HEADERS
                )
                
                if response.status_code == 200:
                    data = response.json()
                    player_data = data.get("data", {})
                    attrs = player_data.get("attributes", {})
                    name = attrs.get("name", "Unknown")
                    
                    print(f"  ✅ ID {pid}: {name}")
                else:
                    print(f"  ❌ ID {pid}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  💥 ID {pid}: {e}")

def check_csv_output():
    """Check the CSV output format"""
    print(f"\n📄 Checking CSV output...")
    
    try:
        df = pd.read_csv("data/wnba_prizepicks_props.csv")
        print(f"Columns: {list(df.columns)}")
        print(f"Shape: {df.shape}")
        
        # Check for player names
        name_cols = [col for col in df.columns if 'name' in col.lower()]
        print(f"Name columns: {name_cols}")
        
        # Show sample data
        print(f"\nSample rows:")
        sample_cols = ['player_id', 'player_name', 'team', 'stat_type', 'line_score']
        available_cols = [col for col in sample_cols if col in df.columns]
        print(df[available_cols].head())
        
        # Check unique players
        if 'player_name' in df.columns:
            unique_names = df['player_name'].value_counts()
            print(f"\nPlayer name distribution:")
            print(unique_names.head(10))
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")

if __name__ == "__main__":
    debug_player_mapping()
    check_csv_output()