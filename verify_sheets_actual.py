#!/usr/bin/env python3
"""Verify Google Sheets data integrity - adapted for your actual sheet structure."""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path.cwd()))

from sheet_connector import SheetConnector

# Get sheet ID from config
import json
sheets_cfg = Path("config/sheets_cfg.json")
if sheets_cfg.exists():
    with open(sheets_cfg) as f:
        SHEET_ID = json.load(f).get('sheet_id', '1-VX73LvsxtpO4D15dsaYso3UjGzYcmsFJUx0io6_VZM')
else:
    SHEET_ID = "1-VX73LvsxtpO4D15dsaYso3UjGzYcmsFJUx0io6_VZM"

OUTPUT_DIR = Path.cwd() / "output"

# Your actual columns based on the test
BETS_LOG_COLUMNS = [
    'source_id', 'timestamp', 'player_name', 'market', 'line', 'phase', 
    'adjusted_prediction', 'wager_amount', 'odds', 'status', 'actual_result', 
    'result_confirmed', 'profit_loss', 'notes'
]

def verify_bets_log(df):
    """Verify bets_log data integrity."""
    issues = []
    
    # Check for missing required columns
    missing_cols = [col for col in ['player_name', 'market', 'line', 'phase', 'wager_amount'] if col not in df.columns]
    if missing_cols:
        issues.append({
            'sheet': 'bets_log',
            'type': 'missing_columns',
            'severity': 'HIGH',
            'message': f"Missing required columns: {missing_cols}"
        })
    
    # Check numeric columns
    if 'wager_amount' in df.columns:
        non_numeric = df[~df['wager_amount'].apply(lambda x: pd.isna(x) or str(x).replace('.','').replace('-','').isdigit())]
        if len(non_numeric) > 0:
            issues.append({
                'sheet': 'bets_log',
                'type': 'data_type',
                'severity': 'MEDIUM',
                'message': f"Non-numeric wager amounts: {len(non_numeric)} rows"
            })
    
    # Check for duplicate entries (same player, market, timestamp)
    if all(col in df.columns for col in ['player_name', 'market', 'timestamp']):
        duplicates = df[df.duplicated(subset=['player_name', 'market', 'timestamp'], keep=False)]
        if len(duplicates) > 0:
            issues.append({
                'sheet': 'bets_log',
                'type': 'duplicate_entries',
                'severity': 'MEDIUM',
                'message': f"Potential duplicate bets: {len(duplicates)} rows"
            })
    
    # Check wager amounts
    if 'wager_amount' in df.columns:
        df['wager_numeric'] = pd.to_numeric(df['wager_amount'], errors='coerce')
        
        # Check for wagers below $5
        low_wagers = df[df['wager_numeric'] < 5]
        if len(low_wagers) > 0:
            issues.append({
                'sheet': 'bets_log',
                'type': 'constraint_violation',
                'severity': 'LOW',
                'message': f"Wagers below $5: {len(low_wagers)} bets"
            })
        
        # Check for suspiciously high wagers
        high_wagers = df[df['wager_numeric'] > 100]
        if len(high_wagers) > 0:
            issues.append({
                'sheet': 'bets_log',
                'type': 'data_validation',
                'severity': 'LOW',
                'message': f"High wagers (>$100): {len(high_wagers)} bets"
            })
    
    return issues

def verify_slips_log(connector):
    """Verify slips_log if it exists."""
    issues = []
    
    try:
        slips_df = connector.read_sheet('slips_log')
        
        # Basic validation since we don't know the exact structure
        if len(slips_df) == 0:
            issues.append({
                'sheet': 'slips_log',
                'type': 'empty_sheet',
                'severity': 'LOW',
                'message': "Slips log is empty"
            })
        else:
            print(f"  Slips log has {len(slips_df)} rows, {len(slips_df.columns)} columns")
            print(f"  Columns: {list(slips_df.columns)[:5]}..." if len(slips_df.columns) > 5 else f"  Columns: {list(slips_df.columns)}")
    
    except Exception as e:
        issues.append({
            'sheet': 'slips_log',
            'type': 'read_error',
            'severity': 'LOW',
            'message': str(e)
        })
    
    return issues

def verify_settings(connector):
    """Verify settings tab."""
    issues = []
    
    try:
        settings = connector.read_sheet('settings')
        
        # Check if bankroll is set
        if 'setting' in settings.columns and 'value' in settings.columns:
            bankroll_row = settings[settings['setting'] == 'bankroll']
            if len(bankroll_row) == 0:
                issues.append({
                    'sheet': 'settings',
                    'type': 'missing_data',
                    'severity': 'MEDIUM',
                    'message': "Bankroll not found in settings"
                })
            else:
                bankroll_value = bankroll_row.iloc[0]['value']
                try:
                    bankroll_float = float(str(bankroll_value).replace('$', '').replace(',', ''))
                    print(f"  Current bankroll: ${bankroll_float:,.2f}")
                except:
                    issues.append({
                        'sheet': 'settings',
                        'type': 'data_conversion',
                        'severity': 'HIGH',
                        'message': f"Cannot parse bankroll value: {bankroll_value}"
                    })
        else:
            print(f"  Settings columns: {list(settings.columns)}")
    
    except Exception as e:
        issues.append({
            'sheet': 'settings',
            'type': 'read_error',
            'severity': 'MEDIUM',
            'message': str(e)
        })
    
    return issues

def main():
    """Main verification process."""
    print("Starting sheet verification...")
    print(f"Sheet ID: {SHEET_ID}")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Connect to sheets
    try:
        connector = SheetConnector(SHEET_ID)
        print("✓ Connected to Google Sheets\n")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return 1
    
    all_issues = []
    
    # Verify bets_log
    print("Verifying bets_log...")
    try:
        bets_df = connector.read_sheet('bets_log')
        print(f"  Found {len(bets_df)} bets")
        
        # Show phase distribution
        if 'phase' in bets_df.columns:
            phase_counts = bets_df['phase'].value_counts()
            print("  Phase distribution:")
            for phase, count in phase_counts.items():
                print(f"    {phase}: {count} bets")
        
        all_issues.extend(verify_bets_log(bets_df))
    except Exception as e:
        all_issues.append({
            'sheet': 'bets_log',
            'type': 'read_error',
            'severity': 'CRITICAL',
            'message': str(e)
        })
    
    # Verify slips_log
    print("\nVerifying slips_log...")
    all_issues.extend(verify_slips_log(connector))
    
    # Verify settings
    print("\nVerifying settings...")
    all_issues.extend(verify_settings(connector))
    
    # Verify phase_confidence_tracker
    print("\nVerifying phase_confidence_tracker...")
    try:
        phase_df = connector.read_sheet('phase_confidence_tracker')
        print(f"  Found {len(phase_df)} phase confidence entries")
    except Exception as e:
        print(f"  Could not read phase_confidence_tracker: {e}")
    
    # Create report
    issues_df = pd.DataFrame(all_issues)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = OUTPUT_DIR / f"sheet_verification_{timestamp}.csv"
    
    if len(issues_df) > 0:
        issues_df.to_csv(output_path, index=False)
        print(f"\n⚠ Verification complete. {len(issues_df)} issues found.")
        print(f"Report saved to: {output_path}")
        
        # Summary by severity
        print("\nIssue Summary:")
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = len(issues_df[issues_df['severity'] == severity])
            if count > 0:
                print(f"  {severity}: {count} issues")
        
        # Show first few issues
        print("\nTop issues:")
        for _, issue in issues_df.head(5).iterrows():
            print(f"  [{issue['severity']}] {issue['sheet']}: {issue['message']}")
    else:
        # Save empty file to indicate success
        issues_df.to_csv(output_path, index=False)
        print("\n✅ Sheet verified - No issues found!")
        print(f"Report saved to: {output_path}")
    
    return 0 if len(issues_df[issues_df['severity'].isin(['CRITICAL', 'HIGH'])]) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())