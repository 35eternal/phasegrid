"""
Data inspection script to understand CSV structure
Path: scripts/data/inspect_data.py
"""

import pandas as pd
from pathlib import Path

def inspect_data():
    # Adjust path for location in scripts/data/
    data_path = Path(__file__).parent.parent.parent / "data" / "wnba_combined_gamelogs.csv"
    
    print("🔍 WNBA Data Inspection")
    print("=" * 40)
    print(f"📂 Looking for: {data_path}")
    
    if not data_path.exists():
        print(f"❌ File not found: {data_path}")
        
        # Check what files do exist in data folder
        data_dir = data_path.parent
        if data_dir.exists():
            print(f"\n📁 Files in {data_dir.name}/ folder:")
            for file in data_dir.iterdir():
                if file.is_file() and file.suffix == '.csv':
                    print(f"  - {file.name}")
        return False
    
    try:
        # Load the data
        df = pd.read_csv(data_path)
        
        print(f"✅ File loaded successfully!")
        print(f"📊 Shape: {df.shape[0]} rows, {df.shape[1]} columns")
        
        print("\n📋 Column Names:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i:2d}. {col}")
        
        print("\n🎯 Looking for player/date/stat columns...")
        
        # Look for player-related columns
        player_cols = [col for col in df.columns if any(word in col.lower() for word in ['player', 'name'])]
        print(f"Player columns: {player_cols}")
        
        # Look for date-related columns  
        date_cols = [col for col in df.columns if any(word in col.lower() for word in ['date', 'game', 'time'])]
        print(f"Date columns: {date_cols}")
        
        # Look for stat columns
        stat_cols = [col for col in df.columns if col in ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG', 'FT', 'Points', 'Rebounds', 'Assists']]
        print(f"Stat columns: {stat_cols}")
        
        print("\n📝 First 3 rows:")
        print(df.head(3))
        
        print("\n💡 Data Types:")
        for col in df.columns[:10]:  # Show first 10 columns
            print(f"  {col}: {df[col].dtype}")
        
        if len(df.columns) > 10:
            print(f"  ... and {len(df.columns) - 10} more columns")
            
        # Check for common WNBA player names
        if player_cols:
            # Prioritize PLAYER_NAME over PLAYER_ID
            player_col = 'PLAYER_NAME' if 'PLAYER_NAME' in df.columns else player_cols[0]
            unique_players = df[player_col].nunique()
            print(f"\n👥 Found {unique_players} unique players")
            
            # Show some player names
            sample_players = df[player_col].dropna().unique()[:5]
            print(f"Sample players: {list(sample_players)}")
        
        # Data quality checks
        print(f"\n📊 DATA QUALITY:")
        print(f"  Missing values: {df.isnull().sum().sum()}")
        print(f"  Duplicate rows: {df.duplicated().sum()}")
        
        if 'GAME_DATE' in df.columns:
            try:
                dates = pd.to_datetime(df['GAME_DATE'], errors='coerce')
                print(f"  Date range: {dates.min()} to {dates.max()}")
                print(f"  Games per day: {df['GAME_DATE'].value_counts().mean():.1f}")
            except:
                print("  Date parsing issues detected")
        
        print(f"\n✅ DATA INSPECTION COMPLETE!")
        return True
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

if __name__ == "__main__":
    import sys
    success = inspect_data()
    sys.exit(0 if success else 1)