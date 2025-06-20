#!/usr/bin/env python3
"""
Simple diagnostic test to figure out WNBA data access.
"""

import pandas as pd
import time
from nba_api.stats.endpoints import playergamelog, commonplayerinfo
from nba_api.stats.static import players

def test_approaches():
    """Test different approaches to access WNBA data."""
    
    print("🔍 NBA API Diagnostic Test\n")
    
    # Test 1: Check if we can get any player data at all
    print("TEST 1: Basic NBA API functionality")
    try:
        # LeBron James (known NBA player)
        lebron_gamelog = playergamelog.PlayerGameLog(player_id=2544, season="2023")
        lebron_df = lebron_gamelog.get_data_frames()[0]
        print(f"✅ LeBron James 2023: {len(lebron_df)} games found")
    except Exception as e:
        print(f"❌ Basic NBA API failed: {e}")
        return
    
    # Test 2: Try with known WNBA player IDs but different seasons
    print("\nTEST 2: WNBA Player IDs with different seasons")
    wnba_test_ids = [1630162, 1630218, 1628886]  # Caitlin Clark, Angel Reese, A'ja Wilson
    wnba_names = ["Caitlin Clark", "Angel Reese", "A'ja Wilson"]
    
    for player_id, name in zip(wnba_test_ids, wnba_names):
        print(f"Testing {name} (ID: {player_id})")
        
        # Try different seasons
        for season in ["2024", "2023", "2022"]:
            try:
                time.sleep(0.5)
                gamelog = playergamelog.PlayerGameLog(
                    player_id=player_id,
                    season=season
                )
                df = gamelog.get_data_frames()[0]
                if not df.empty:
                    print(f"  ✅ {season}: Found {len(df)} games")
                    # Show a sample game
                    if len(df) > 0:
                        sample = df.iloc[0]
                        print(f"    Sample: {sample['GAME_DATE']} vs {sample['MATCHUP']} - {sample['PTS']} pts")
                else:
                    print(f"  ⚠️ {season}: Empty dataframe")
            except Exception as e:
                print(f"  ❌ {season}: {e}")
    
    # Test 3: Check player info for WNBA players
    print("\nTEST 3: Player info lookup")
    for player_id, name in zip(wnba_test_ids, wnba_names):
        try:
            time.sleep(0.5)
            player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
            info_df = player_info.get_data_frames()[0]
            if not info_df.empty:
                player_data = info_df.iloc[0]
                print(f"✅ {name}: Team={player_data.get('TEAM_NAME', 'N/A')}, Active={player_data.get('ROSTERSTATUS', 'N/A')}")
            else:
                print(f"⚠️ {name}: No player info found")
        except Exception as e:
            print(f"❌ {name}: {e}")
    
    # Test 4: Try to find WNBA players in the static players list
    print("\nTEST 4: Search static player database")
    try:
        all_players = players.get_players()
        wnba_search_names = ["Caitlin Clark", "A'ja Wilson", "Angel Reese", "Diana Taurasi"]
        
        for search_name in wnba_search_names:
            found_players = [p for p in all_players if search_name.lower() in p['full_name'].lower()]
            if found_players:
                for player in found_players:
                    print(f"✅ Found: {player['full_name']} (ID: {player['id']})")
            else:
                print(f"❌ Not found: {search_name}")
                
    except Exception as e:
        print(f"❌ Static search failed: {e}")
    
    print("\n📋 SUMMARY:")
    print("If you see ✅ marks above, the NBA API is working but may not have WNBA data")
    print("If you see all ❌ marks, there might be a different issue")

if __name__ == "__main__":
    test_approaches()