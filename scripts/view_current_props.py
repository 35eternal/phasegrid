#!/usr/bin/env python3
"""
View current PrizePicks WNBA props data
"""

import json
import csv
from pathlib import Path
from datetime import datetime
import pandas as pd

# Get project root
project_root = Path(__file__).parent.parent.parent
data_dir = project_root / "data"

print("🏀 Current WNBA PrizePicks Props")
print("=" * 50)

# Check CSV file
csv_file = data_dir / "wnba_prizepicks_props.csv"
json_file = data_dir / "wnba_prizepicks_props.json"

# Read and display CSV data
if csv_file.exists():
    print(f"\n📄 Reading: {csv_file.name}")
    print(f"Modified: {datetime.fromtimestamp(csv_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Use pandas for nice display
    try:
        df = pd.read_csv(csv_file)
        print(f"\nTotal props: {len(df)}")
        
        # Show data summary
        print("\n📊 Data Summary:")
        print(f"Players: {df['player_name'].nunique() if 'player_name' in df else 'N/A'}")
        
        if 'stat_type' in df:
            print("\nStat types available:")
            for stat, count in df['stat_type'].value_counts().items():
                print(f"  - {stat}: {count} props")
        
        # Show sample data
        print("\n📋 Sample Props (first 10):")
        print("-" * 80)
        
        for idx, row in df.head(10).iterrows():
            player = row.get('player_name', 'Unknown')
            stat = row.get('stat_type', 'Unknown')
            line = row.get('line', 'N/A')
            team = row.get('team_name', '')
            
            print(f"{idx+1:2d}. {player:<25} {stat:<20} {line:>6} {team}")
            
        # Check for specific players
        print("\n🔍 Quick player search:")
        search_players = ["A'ja Wilson", "Breanna Stewart", "Caitlin Clark", "Angel Reese"]
        for player in search_players:
            if 'player_name' in df.columns:
                matches = df[df['player_name'].str.contains(player, case=False, na=False)]
                if not matches.empty:
                    print(f"\n{player}:")
                    for _, row in matches.iterrows():
                        print(f"  - {row['stat_type']}: {row['line']}")
                        
    except Exception as e:
        print(f"Error with pandas: {e}")
        # Fallback to basic reading
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            print(f"\nTotal props: {len(rows)}")
            
            print("\nFirst 5 props:")
            for i, row in enumerate(rows[:5]):
                print(f"{i+1}. {row}")

# Check JSON file for additional info
if json_file.exists():
    print(f"\n\n📄 JSON file also available: {json_file.name}")
    with open(json_file, 'r') as f:
        data = json.load(f)
        if isinstance(data, list) and len(data) > 0:
            print(f"Contains {len(data)} records")
            
print("\n\n✅ Data is ready for use!")
print("You can now run your prediction models with this fresh data.")