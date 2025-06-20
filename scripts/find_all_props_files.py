#!/usr/bin/env python3
"""
Find all props files anywhere in the project
"""

import os
from pathlib import Path

# Start from current directory
start_path = Path.cwd()

print("🔍 Searching for PrizePicks/props files...")
print(f"Starting from: {start_path}\n")

# Search patterns
patterns = ['*prizepicks*.csv', '*prizepicks*.json', '*props*.csv', '*props*.json']
found_files = []

# Search in current directory and all subdirectories
for pattern in patterns:
    for file in start_path.rglob(pattern):
        # Skip node_modules, venv, etc.
        skip_dirs = ['node_modules', 'venv', '__pycache__', '.git']
        if not any(skip in str(file) for skip in skip_dirs):
            found_files.append(file)

# Remove duplicates and sort by modification time
found_files = list(set(found_files))
found_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

if found_files:
    print(f"✅ Found {len(found_files)} files:\n")
    
    for file in found_files[:15]:  # Show first 15
        # Get relative path from current directory
        try:
            rel_path = file.relative_to(start_path)
        except:
            rel_path = file
            
        # Get file info
        size_kb = file.stat().st_size / 1024
        
        print(f"📄 {rel_path}")
        print(f"   Size: {size_kb:.1f} KB")
        
        # Try to peek at content
        try:
            if file.suffix == '.csv':
                with open(file, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    second_line = f.readline().strip()
                    print(f"   Headers: {first_line[:100]}...")
                    if second_line:
                        print(f"   First row: {second_line[:100]}...")
            elif file.suffix == '.json':
                with open(file, 'r', encoding='utf-8') as f:
                    import json
                    data = json.load(f)
                    if isinstance(data, list):
                        print(f"   Array with {len(data)} items")
                    elif isinstance(data, dict):
                        print(f"   Object with keys: {list(data.keys())[:5]}...")
        except Exception as e:
            print(f"   Cannot read: {e}")
            
        print()
else:
    print("❌ No props files found!")
    
print("\n💡 If files are missing, they might be in:")
print("  - A different project folder")
print("  - The 'wnba_predictor copy' parent directory")
print("  - A backup directory")