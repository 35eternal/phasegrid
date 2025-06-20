#!/usr/bin/env python3
"""
Find and display all PrizePicks data files
"""

import os
from pathlib import Path
from datetime import datetime
import json
import csv

# Get project root
project_root = Path(__file__).parent.parent.parent
data_dir = project_root / "data"

print("🔍 Searching for PrizePicks data files...")
print(f"Looking in: {data_dir}\n")

# Find all files with prizepicks or props in the name
all_files = []
if data_dir.exists():
    for file in data_dir.iterdir():
        if file.is_file():
            name_lower = file.name.lower()
            if 'prizepicks' in name_lower or 'props' in name_lower:
                all_files.append(file)

if not all_files:
    print("❌ No PrizePicks data files found!")
    print("\nLet's check all CSV and JSON files in data directory:")
    for file in data_dir.glob("*.csv"):
        print(f"  - {file.name}")
    for file in data_dir.glob("*.json"):
        print(f"  - {file.name}")
else:
    # Sort by modification time (newest first)
    all_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    print(f"✅ Found {len(all_files)} PrizePicks-related files:\n")
    
    for file in all_files:
        # Get file info
        stats = file.stat()
        mod_time = datetime.fromtimestamp(stats.st_mtime)
        size_kb = stats.st_size / 1024
        
        print(f"📄 {file.name}")
        print(f"   Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Size: {size_kb:.1f} KB")
        
        # Try to read and show sample data
        try:
            if file.suffix == '.json':
                with open(file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        print(f"   Records: {len(data)}")
                        # Show first record
                        first = data[0]
                        if isinstance(first, dict):
                            print(f"   Sample: {list(first.keys())}")
                            
            elif file.suffix == '.csv':
                with open(file, 'r') as f:
                    reader = csv.reader(f)
                    headers = next(reader, None)
                    if headers:
                        print(f"   Columns: {headers}")
                    # Count rows
                    row_count = sum(1 for row in reader)
                    print(f"   Records: {row_count}")
                    
        except Exception as e:
            print(f"   Error reading: {e}")
            
        print()

print("\n💡 Next steps:")
print("1. If files exist, use the most recent one")
print("2. If rate limited, wait 30-60 minutes")
print("3. Or use: python scripts/scraping/rate_limit_aware_scraper.py")