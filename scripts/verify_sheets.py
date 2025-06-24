#!/usr/bin/env python3
"""Verify PhaseGrid Google Sheets setup and data integrity."""

import sys
import os
# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime
from modules.sheet_connector import BetSyncSheetConnector

# Expected tabs and columns
EXPECTED_TABS = ['bets_log', 'slips_log', 'phase_tracker', 'settings']

EXPECTED_COLUMNS = {
    'bets_log': ['source_id', 'date', 'player', 'stat', 'line', 'over_under', 
                 'confidence', 'phase', 'result', 'updated'],
    'slips_log': ['slip_id', 'date', 'type', 'legs', 'stake', 'ev', 'phase', 
                  'result', 'payout', 'created', 'updated'],
    'phase_tracker': ['date', 'phase', 'total_bets', 'winning_bets', 'total_stakes',
                      'total_payouts', 'roi', 'updated'],
    'settings': ['setting', 'value', 'description', 'updated']
}

def verify_sheets():
    """Main verification function."""
    print("=" * 60)
    print("PhaseGrid Google Sheets Verification")
    print("=" * 60)
    
    # Initialize connector
    sheet_id = os.getenv("SHEET_ID")
    if not sheet_id:
        print("❌ ERROR: SHEET_ID not found in environment variables")
        print("   Please set SHEET_ID in your .env file")
        return False
    
    print(f"Sheet ID: {sheet_id}")
    print()
    
    try:
        connector = BetSyncSheetConnector(sheet_id=sheet_id)
        print("✅ Successfully connected to Google Sheets")
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to Google Sheets")
        print(f"   {str(e)}")
        return False
    
    # Verify tabs exist
    print("\nVerifying tabs...")
    try:
        all_tabs = connector.get_all_tabs()
        tab_names = [tab.title for tab in all_tabs]
        
        for expected_tab in EXPECTED_TABS:
            if expected_tab in tab_names:
                print(f"  ✅ Tab '{expected_tab}' exists")
            else:
                print(f"  ❌ Tab '{expected_tab}' is missing")
                print(f"     Creating tab '{expected_tab}'...")
                try:
                    connector.create_tab_if_not_exists(expected_tab)
                    print(f"     ✅ Created tab '{expected_tab}'")
                except Exception as e:
                    print(f"     ❌ Failed to create tab: {str(e)}")
    except Exception as e:
        print(f"❌ ERROR: Failed to verify tabs")
        print(f"   {str(e)}")
        return False
    
    # Verify columns in each tab
    print("\nVerifying columns...")
    for tab_name, expected_cols in EXPECTED_COLUMNS.items():
        try:
            df = connector.read_sheet(tab_name)
            if df.empty:
                print(f"  ⚠️  Tab '{tab_name}' is empty - initializing with headers")
                # Create empty dataframe with expected columns
                init_df = pd.DataFrame(columns=expected_cols)
                connector.write_sheet(init_df, tab_name)
                print(f"     ✅ Initialized '{tab_name}' with headers")
            else:
                existing_cols = list(df.columns)
                missing_cols = [col for col in expected_cols if col not in existing_cols]
                extra_cols = [col for col in existing_cols if col not in expected_cols]
                
                if not missing_cols and not extra_cols:
                    print(f"  ✅ Tab '{tab_name}' has correct columns")
                else:
                    if missing_cols:
                        print(f"  ❌ Tab '{tab_name}' missing columns: {missing_cols}")
                    if extra_cols:
                        print(f"  ⚠️  Tab '{tab_name}' has extra columns: {extra_cols}")
        except Exception as e:
            print(f"  ❌ ERROR verifying tab '{tab_name}': {str(e)}")
    
    # Test write permissions
    print("\nTesting write permissions...")
    try:
        test_df = pd.DataFrame([{
            'setting': 'test_verification',
            'value': str(datetime.now()),
            'description': 'Automated verification test',
            'updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }])
        
        # Read current settings
        settings_df = connector.read_sheet('settings')
        
        # Remove any existing test entries
        if not settings_df.empty:
            settings_df = settings_df[settings_df['setting'] != 'test_verification']
        
        # Add test entry
        settings_df = pd.concat([settings_df, test_df], ignore_index=True)
        
        # Write back
        connector.write_sheet(settings_df, 'settings')
        print("  ✅ Write permissions verified")
        
        # Clean up test entry
        settings_df = settings_df[settings_df['setting'] != 'test_verification']
        connector.write_sheet(settings_df, 'settings')
        
    except Exception as e:
        print(f"  ❌ ERROR: Write test failed - {str(e)}")
        print("     This might indicate read-only access")
    
    print("\n" + "=" * 60)
    print("Verification complete!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    verify_sheets()