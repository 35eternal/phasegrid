#!/usr/bin/env python3
"""
Check and display PrizePicks data from various sources
"""

import json
import csv
from pathlib import Path
import glob

# Find project root
project_root = Path(__file__).parent.parent.parent
data_dir = project_root / "data"

print("🔍 Searching for PrizePicks data files...\n")

# Look for all relevant files
patterns = [
    "*prizepicks*.json",
    "*prizepicks*.csv",
    "*props*.json",
    "*props*.csv"
]

found_files = []
for pattern in patterns:
    found_files.extend(data_dir.glob(pattern))

# Check each file
for file_path in sorted(set(found_files)):
    print(f"\n📄 {file_path.name}")
    print(f"   Modified: {file_path.stat().st_mtime}")
    
    try:
        if file_path.suffix == '.json':
            with open(file_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    print(f"   Total props: {len(data)}")
                    print(f"   Sample data:")
                    for i, prop in enumerate(data[:3]):
                        if isinstance(prop, dict):
                            player = prop.get('player_name', prop.get('playerName', 'Unknown'))
                            stat = prop.get('stat_type', prop.get('statType', prop.get('market', 'Unknown')))
                            line = prop.get('line', prop.get('projection', 'N/A'))
                            print(f"     {i+1}. {player} - {stat}: {line}")
                        
        elif file_path.suffix == '.csv':
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if rows:
                    print(f"   Total props: {len(rows)}")
                    print(f"   Sample data:")
                    for i, row in enumerate(rows[:3]):
                        player = row.get('player_name', row.get('playerName', 'Unknown'))
                        stat = row.get('stat_type', row.get('statType', 'Unknown'))
                        line = row.get('line', row.get('projection', 'N/A'))
                        print(f"     {i+1}. {player} - {stat}: {line}")
                        
    except Exception as e:
        print(f"   Error reading file: {e}")

print("\n\n💡 Recommendation:")
print("Use: python scripts/scraping/fetch_prizepicks_props.py")
print("This is your working scraper that successfully fetches data!")