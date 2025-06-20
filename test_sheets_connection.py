#!/usr/bin/env python3
"""Simple test to verify Google Sheets connection works."""

import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path.cwd()))

print("Testing Google Sheets connection...")
print(f"Current directory: {Path.cwd()}")

try:
    from sheet_connector import SheetConnector
    print("✓ Sheet connector imported successfully")
    
    # Check for sheet ID in config
    sheets_cfg = Path("config/sheets_cfg.json")
    if sheets_cfg.exists():
        import json
        with open(sheets_cfg) as f:
            cfg = json.load(f)
            sheet_id = cfg.get('sheet_id', '1-VX73LvsxtpO4D15dsaYso3UjGzYcmsFJUx0io6_VZM')
            print(f"✓ Found sheet ID in config: {sheet_id}")
    else:
        sheet_id = "1-VX73LvsxtpO4D15dsaYso3UjGzYcmsFJUx0io6_VZM"
        print(f"Using default sheet ID: {sheet_id}")
    
    # Try to connect
    print("\nAttempting connection...")
    connector = SheetConnector(sheet_id)
    print("✓ Connected to Google Sheets!")
    
    # List available tabs
    tabs = connector.get_all_tabs()
    print(f"\nFound {len(tabs)} tabs:")
    for tab in tabs:
        print(f"  - {tab}")
    
    # Try to read bets_log
    print("\nTesting read from bets_log...")
    try:
        bets_df = connector.read_sheet('bets_log')
        print(f"✓ Successfully read bets_log: {len(bets_df)} rows, {len(bets_df.columns)} columns")
        print(f"Columns: {list(bets_df.columns)}")
    except Exception as e:
        print(f"✗ Error reading bets_log: {e}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()