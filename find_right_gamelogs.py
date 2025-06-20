import pandas as pd
import os

print("🔍 Finding the right gamelogs file...")
print("=" * 60)

# List of potential gamelog files
potential_files = [
    'data/processed/merged_props_with_gamelogs.csv',
    'data/unified_gamelogs.csv',
    'data/unified_gamelogs_with_features.csv',
    'data/unified_gamelogs_boosted.csv',
    'data/wnba_combined_gamelogs.csv',
    'data/wnba_full_gamelogs.csv',
    'data/wnba_current_gamelogs.csv',
    'data/wnba_2024_gamelogs.csv',
    'data/archive/2024/engineered_gamelogs_2024.csv',
    'data/archive/2024/cleaned_gamelogs_2024.csv'
]

# Check each file
found_gamelogs = False
for filepath in potential_files:
    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath)
            print(f"\n📄 {filepath}")
            print(f"   Rows: {len(df)}")
            print(f"   Columns: {list(df.columns)[:10]}")  # First 10 columns
            
            # Check for key stat columns
            stat_cols = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG', 'FGA', '3P', '3PA']
            found_stats = [col for col in stat_cols if col in df.columns]
            
            if found_stats:
                print(f"   ✅ Found stats: {found_stats}")
                print(f"   👤 Potential player columns: {[col for col in df.columns if 'player' in col.lower() or 'name' in col.lower()]}")
                found_gamelogs = True
            else:
                print(f"   ❌ No game stats found")
                
        except Exception as e:
            print(f"   ⚠️  Error reading: {e}")

if not found_gamelogs:
    print("\n⚠️  No files with actual game statistics found!")
    print("\nLet's check what CSV files exist in the data directory:")
    
    # List all CSV files in data directory
    data_dir = 'data'
    if os.path.exists(data_dir):
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        print(f"\nCSV files in {data_dir}:")
        for f in csv_files[:20]:  # First 20 files
            print(f"  - {f}")