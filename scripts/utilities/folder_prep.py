#!/usr/bin/env python3
"""
Folder preparation script for nightly betting system maintenance.
Archives current day's betting card and creates fresh structure.
"""

import os
import shutil
from datetime import datetime
import pandas as pd

def create_folder_structure():
    """Ensure all required folders exist."""
    folders = [
        'input',
        'output', 
        'archived_cards',
        'archived_results',
        'phase_logs',
        'config',
        'checklists',
        'scripts/utilities',
        'scripts/tools'
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"✅ Ensured folder exists: {folder}")

def archive_daily_card():
    """Archive today's betting card with proper naming."""
    source_file = 'daily_betting_card_adjusted.csv'
    
    if os.path.exists(source_file):
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        archive_path = f'archived_cards/daily_card_{today}.csv'
        
        # Copy file to archive
        shutil.copy2(source_file, archive_path)
        print(f"✅ Archived: {source_file} → {archive_path}")
        
        # Remove original
        os.remove(source_file)
        print(f"✅ Removed original: {source_file}")
    else:
        print(f"⚠️  No file found to archive: {source_file}")

def create_empty_betting_card():
    """Create fresh empty betting card with proper structure."""
    # Define expected columns for betting card
    columns = [
        'source_id', 'date', 'game', 'player', 'market', 'line',
        'prediction', 'odds', 'confidence', 'phase', 'kelly_fraction',
        'recommended_bet_size', 'actual_result', 'profit_loss'
    ]
    
    # Create empty DataFrame
    empty_df = pd.DataFrame(columns=columns)
    
    # Save to input folder
    output_path = 'input/daily_betting_card.csv'
    empty_df.to_csv(output_path, index=False)
    print(f"✅ Created empty betting card: {output_path}")

def main():
    """Execute folder preparation tasks."""
    print("🎯 Starting Folder Preparation...")
    print("-" * 50)
    
    # Create folder structure
    create_folder_structure()
    print()
    
    # Archive today's card
    archive_daily_card()
    print()
    
    # Create fresh empty card
    create_empty_betting_card()
    print()
    
    print("✅ Folder preparation complete!")

if __name__ == "__main__":
    main()
