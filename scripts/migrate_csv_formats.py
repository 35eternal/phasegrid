"""
CSV Format Migration Script
Converts legacy simulation files to new paper trader schema
"""
import pandas as pd
import os
import glob
from datetime import datetime
import shutil

def migrate_csv_formats():
    """Migrate old CSV formats to new paper trader schema"""
    
    # Create backup directory
    backup_dir = f"data/legacy_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Define column mappings
    column_mappings = {
        'bet_id': 'event_id',
        'predicted_outcome': 'prediction',
        'confidence_score': 'confidence',
        'betting_odds': 'odds',
        'player': 'player_name',
        'prop_type': 'market',
        'line_value': 'line',
        'actual_outcome': 'result',
        'bet_amount': 'stake',
        'payout': 'profit'
    }
    
    # Find all CSV files that might need migration
    patterns = [
        'output/simulation_*.csv',
        'output/backtest_*.csv',
        'data/*_results.csv'
    ]
    
    migrated_count = 0
    
    for pattern in patterns:
        for filepath in glob.glob(pattern):
            try:
                # Read the CSV
                df = pd.read_csv(filepath)
                
                # Check if migration needed
                if 'bet_id' in df.columns or 'predicted_outcome' in df.columns:
                    print(f"Migrating: {filepath}")
                    
                    # Backup original
                    backup_path = os.path.join(backup_dir, os.path.basename(filepath))
                    shutil.copy2(filepath, backup_path)
                    
                    # Rename columns
                    df.rename(columns=column_mappings, inplace=True)
                    
                    # Add missing required columns with defaults
                    if 'event_id' not in df.columns and 'bet_id' not in df.columns:
                        df['event_id'] = range(1, len(df) + 1)
                    
                    if 'confidence' not in df.columns:
                        df['confidence'] = 0.65  # Default confidence
                    
                    if 'odds' not in df.columns:
                        df['odds'] = -110  # Default odds
                    
                    if 'timestamp' not in df.columns:
                        df['timestamp'] = datetime.now().isoformat()
                    
                    # Ensure correct column order
                    required_columns = ['event_id', 'player_name', 'market', 'line', 
                                      'prediction', 'confidence', 'odds', 'stake', 
                                      'result', 'profit', 'timestamp']
                    
                    # Add any missing columns
                    for col in required_columns:
                        if col not in df.columns:
                            if col == 'stake':
                                df[col] = 10.0  # Default stake
                            elif col == 'profit':
                                df[col] = 0.0
                            elif col == 'result':
                                df[col] = 'pending'
                            else:
                                df[col] = ''
                    
                    # Reorder columns
                    df = df[required_columns + [col for col in df.columns if col not in required_columns]]
                    
                    # Save migrated file
                    df.to_csv(filepath, index=False)
                    migrated_count += 1
                    print(f"  ✓ Migrated successfully")
                    
            except Exception as e:
                print(f"  ✗ Error migrating {filepath}: {e}")
    
    print(f"\nMigration complete!")
    print(f"Files migrated: {migrated_count}")
    print(f"Backups saved to: {backup_dir}")
    
    return migrated_count

if __name__ == "__main__":
    migrate_csv_formats()