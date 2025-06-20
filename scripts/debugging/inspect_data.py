import pandas as pd

def inspect_historical_data():
    print('🔍 INSPECTING HISTORICAL DATA STRUCTURE')
    
    try:
        df = pd.read_csv('data/wnba_2024_gamelogs.csv')
        print(f'📊 Loaded {len(df)} rows')
        print(f'📋 Columns: {list(df.columns)}')
        print(f'\n🔍 First few rows:')
        print(df.head())
        
        # Look for player name columns
        possible_name_cols = [col for col in df.columns if 'name' in col.lower() or 'player' in col.lower()]
        print(f'\n👤 Possible player name columns: {possible_name_cols}')
        
        # Show sample of first column (likely player names)
        if len(df.columns) > 0:
            first_col = df.columns[0]
            print(f'\n📝 Sample from first column "{first_col}":')
            print(df[first_col].head(10).tolist())
            
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == '__main__':
    inspect_historical_data()
