#!/usr/bin/env python3
"""
Simple script to view PrizePicks props data
"""

import json
import csv
from pathlib import Path
import os

# Get project root
project_root = Path(__file__).parent.parent.parent
data_dir = project_root / "data"

print("🏀 Searching for WNBA PrizePicks Props")
print("=" * 50)
print(f"Looking in: {data_dir}\n")

# List all files in data directory first
print("📁 Files in data directory:")
if data_dir.exists():
    files = list(data_dir.glob("*"))
    for f in sorted(files)[:20]:  # Show first 20 files
        if f.is_file():
            print(f"  - {f.name}")
else:
    print("  ❌ Data directory not found!")

print("\n" + "=" * 50 + "\n")

# Look for specific files
files_to_check = [
    "wnba_prizepicks_props.csv",
    "wnba_prizepicks_props.json",
    "prizepicks_wnba_props.csv",
    "prizepicks_props.csv",
    "merged_props.csv"
]

found_any = False

for filename in files_to_check:
    filepath = data_dir / filename
    if filepath.exists():
        found_any = True
        print(f"\n📄 Found: {filename}")
        print(f"   Size: {filepath.stat().st_size} bytes")
        
        try:
            if filename.endswith('.csv'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    
                    if rows:
                        print(f"   Rows: {len(rows)}")
                        print(f"   Columns: {list(rows[0].keys())}")
                        
                        print("\n   First 5 entries:")
                        for i, row in enumerate(rows[:5]):
                            player = row.get('player_name', row.get('playerName', 'Unknown'))
                            stat = row.get('stat_type', row.get('statType', 'Unknown'))
                            line = row.get('line', row.get('projection', 'N/A'))
                            print(f"   {i+1}. {player} - {stat}: {line}")
                            
            elif filename.endswith('.json'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if isinstance(data, list):
                        print(f"   Items: {len(data)}")
                        if data and isinstance(data[0], dict):
                            print(f"   Keys: {list(data[0].keys())}")
                            
                            print("\n   First 3 entries:")
                            for i, item in enumerate(data[:3]):
                                print(f"   {i+1}. {json.dumps(item, indent=6)[:200]}...")
                                
        except Exception as e:
            print(f"   ❌ Error reading: {e}")

if not found_any:
    print("\n❌ No PrizePicks data files found!")
    print("\n🔧 Try running:")
    print("   python scripts/scraping/fetch_prizepicks_props.py")
    print("   (after rate limit expires)")
else:
    print("\n\n✅ Data found and ready to use!")