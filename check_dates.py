import pandas as pd
import os

def main():
    """Check date formats in the data files."""
    # Try to find a data file with dates
    data_files = [
        "data/wnba_combined_gamelogs.csv",
        "data/sample_data.csv",
        "bets_log.csv"
    ]
    
    for file_path in data_files:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            print(f"Checking {file_path}...")
            
            # Look for date columns
            date_columns = [col for col in df.columns if 'date' in col.lower() or 'game' in col.lower()]
            
            if date_columns:
                for col in date_columns:
                    print(f"\nColumn '{col}':")
                    print(f"  Sample values: {df[col].head(3).tolist()}")
                    print(f"  Unique count: {df[col].nunique()}")
                    if 'GAME_DATE' in df.columns:
                        print(f"  Date range: {df['GAME_DATE'].min()} to {df['GAME_DATE'].max()}")
            else:
                print(f"  No date columns found in {file_path}")
            break
    else:
        # Create a sample DataFrame if no files exist
        df = pd.DataFrame({
            'GAME_DATE': pd.date_range('2024-01-01', periods=10, freq='D'),
            'Player': ['Player A'] * 10,
            'PTS': [20] * 10
        })
        print("Using sample data for testing")
        print(df['GAME_DATE'].head(10).tolist())

if __name__ == "__main__":
    main()
