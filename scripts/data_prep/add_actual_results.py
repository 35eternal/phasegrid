#!/usr/bin/env python3
"""
add_actual_results.py

Helps add actual game results to predictions for validation.
Can use manual entry, API data, or simulated results for testing.

Place in: scripts/data_prep/add_actual_results.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def add_simulated_results(df):
    """
    Add simulated results for testing the validation pipeline.
    In production, replace this with actual game data.
    """
    logger.info("Adding simulated results for testing...")
    
    # Simulate results based on predictions with some noise
    # This creates realistic test data where predictions are somewhat accurate
    np.random.seed(42)  # For reproducibility
    
    actual_results = []
    for idx, row in df.iterrows():
        prediction = row['adjusted_prediction']
        line = row['line']
        
        # Add noise based on stat type volatility
        if row['stat_type'] == 'points':
            noise_std = 4.0
        elif row['stat_type'] == 'assists':
            noise_std = 2.0
        elif row['stat_type'] == 'rebounds':
            noise_std = 3.0
        elif row['stat_type'] == '3ptm':
            noise_std = 1.5
        else:
            noise_std = 2.5
        
        # Add extra volatility for certain phases/risk tags
        if row['adv_risk_tag'] == 'FADE_LUTEAL':
            noise_std *= 1.3
        elif row['adv_risk_tag'] == 'TARGET_OVULATION':
            noise_std *= 0.9
        
        # Generate actual result
        noise = np.random.normal(0, noise_std)
        actual = prediction + noise
        
        # Ensure non-negative values
        actual = max(0, actual)
        
        # Round based on stat type
        if row['stat_type'] in ['points', 'assists', 'rebounds', '3ptm']:
            actual = round(actual)
        else:
            actual = round(actual, 1)
        
        actual_results.append(actual)
    
    df['actual_result'] = actual_results
    return df


def add_manual_results(df):
    """
    Interactive function to manually add results for specific games.
    Useful for adding real results as games complete.
    """
    logger.info("Manual result entry mode...")
    
    # Initialize actual_result column if it doesn't exist
    if 'actual_result' not in df.columns:
        df['actual_result'] = np.nan
    
    # Show props that need results
    missing_results = df[df['actual_result'].isna()]
    
    if len(missing_results) == 0:
        logger.info("All props already have results!")
        return df
    
    print(f"\nFound {len(missing_results)} props without results.")
    print("Enter results (or 'skip' to skip, 'done' to finish):\n")
    
    for idx, row in missing_results.iterrows():
        print(f"\n{row['player_name']} - {row['stat_type']}")
        print(f"Line: {row['line']}, Your prediction: {row['adjusted_prediction']}")
        
        while True:
            result = input("Actual result: ").strip()
            
            if result.lower() == 'done':
                return df
            elif result.lower() == 'skip':
                break
            
            try:
                actual = float(result)
                df.at[idx, 'actual_result'] = actual
                print(f"✓ Recorded: {actual}")
                break
            except ValueError:
                print("Please enter a valid number, 'skip', or 'done'")
    
    return df


def add_results_from_api(df, api_data_file=None):
    """
    Add results from an API data file or external source.
    This is a placeholder - implement based on your data source.
    """
    logger.info("Adding results from external data source...")
    
    # Example implementation for CSV-based results
    if api_data_file and Path(api_data_file).exists():
        results_df = pd.read_csv(api_data_file)
        
        # Merge on player_name, stat_type, and game_date if available
        # Adjust merge keys based on your data structure
        df = df.merge(
            results_df[['player_name', 'stat_type', 'actual_result']], 
            on=['player_name', 'stat_type'],
            how='left',
            suffixes=('', '_new')
        )
        
        # Update actual_result where we have new data
        if 'actual_result_new' in df.columns:
            df['actual_result'] = df['actual_result'].fillna(df['actual_result_new'])
            df.drop('actual_result_new', axis=1, inplace=True)
    
    return df


def main():
    """Main execution function."""
    # Paths
    project_root = Path.cwd()
    input_file = project_root / 'data' / 'final_props_with_advanced_cycles.csv'
    output_file = project_root / 'data' / 'final_props_with_advanced_cycles.csv'
    
    # Load data
    logger.info(f"Loading predictions from {input_file}")
    df = pd.read_csv(input_file)
    
    print("\nHow would you like to add actual results?")
    print("1. Simulate results (for testing)")
    print("2. Manual entry")
    print("3. Load from external file")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        df = add_simulated_results(df)
        logger.info("Simulated results added successfully!")
    
    elif choice == '2':
        df = add_manual_results(df)
        logger.info("Manual results added!")
    
    elif choice == '3':
        api_file = input("Enter path to results file (or press Enter to skip): ").strip()
        if api_file:
            df = add_results_from_api(df, api_file)
        else:
            logger.warning("No file provided, skipping...")
    
    else:
        logger.error("Invalid choice!")
        return
    
    # Save updated data
    df.to_csv(output_file, index=False)
    logger.info(f"Updated data saved to {output_file}")
    
    # Show summary
    if 'actual_result' in df.columns:
        completed = df['actual_result'].notna().sum()
        total = len(df)
        logger.info(f"Results status: {completed}/{total} props have actual results")


if __name__ == "__main__":
    main()