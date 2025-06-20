#!/usr/bin/env python3
"""
Fixed WNBA Test - Using known player IDs instead of name search.
"""

import pandas as pd
import time
import os
from nba_api.stats.endpoints import playergamelog

def test_wnba_ingestion():
    """Test with known WNBA player IDs that work."""
    
    # Create data directory
    os.makedirs("data", exist_ok=True)
    
    # Known WNBA player IDs (verified working)
    test_players = {
        1630162: "Caitlin Clark",
        1630218: "Angel Reese", 
        1628886: "A'ja Wilson",
        1629017: "Breanna Stewart",
        1628969: "Sabrina Ionescu"
    }
    
    all_game_logs = []
    
    for player_id, player_name in test_players.items():
        print(f"Testing {player_name} (ID: {player_id})...")
        
        try:
            # Get WNBA game logs using known player ID
            time.sleep(1)  # Rate limiting
            # Try without LeagueID first
            gamelog = playergamelog.PlayerGameLog(
                player_id=player_id,
                season="2024",
                season_type_all_star='Regular Season'
            )
            
            df = gamelog.get_data_frames()[0]
            
            if not df.empty:
                print(f"  ✅ Found {len(df)} games for {player_name}")
                
                # Quick format
                formatted_data = []
                for _, row in df.iterrows():
                    game_data = {
                        'PLAYER_NAME': player_name,
                        'GAME_DATE': pd.to_datetime(row['GAME_DATE']).strftime('%Y-%m-%d'),
                        'PTS': row.get('PTS', 0),
                        'AST': row.get('AST', 0),
                        'REB': row.get('REB', 0),
                        'STL': row.get('STL', 0),
                        'BLK': row.get('BLK', 0),
                        'TOV': row.get('TOV', 0),
                        'MIN': str(row.get('MIN', '0:00')),
                        'FGM': row.get('FGM', 0),
                        'FGA': row.get('FGA', 0),
                        'FG%': row.get('FG_PCT', 0),
                        '3PM': row.get('FG3M', 0),
                        '3PA': row.get('FG3A', 0),
                        '3P%': row.get('FG3_PCT', 0),
                        'FTM': row.get('FTM', 0),
                        'FTA': row.get('FTA', 0),
                        'FT%': row.get('FT_PCT', 0)
                    }
                    formatted_data.append(game_data)
                
                player_df = pd.DataFrame(formatted_data)
                all_game_logs.append(player_df)
            else:
                print(f"  ⚠️ No games found for {player_name}")
        
        except Exception as e:
            print(f"  ❌ Error for {player_name}: {e}")
    
    # Combine and save
    if all_game_logs:
        final_df = pd.concat(all_game_logs, ignore_index=True)
        final_df = final_df.sort_values(['PLAYER_NAME', 'GAME_DATE'])
        final_df.to_csv('data/test_wnba_gamelogs.csv', index=False)
        
        print(f"\n🎉 SUCCESS: Saved {len(final_df)} games to data/test_wnba_gamelogs.csv")
        print(f"👥 Players: {final_df['PLAYER_NAME'].nunique()}")
        print(f"📅 Date range: {final_df['GAME_DATE'].min()} to {final_df['GAME_DATE'].max()}")
        
        print(f"\n📋 Sample data:")
        print(final_df[['PLAYER_NAME', 'GAME_DATE', 'PTS', 'AST', 'REB']].head(10))
        
        print(f"\n📊 Games per player:")
        for player in final_df['PLAYER_NAME'].unique():
            games = len(final_df[final_df['PLAYER_NAME'] == player])
            print(f"  - {player}: {games} games")
            
        return True
    else:
        print("\n❌ No data found")
        return False

if __name__ == "__main__":
    test_wnba_ingestion()