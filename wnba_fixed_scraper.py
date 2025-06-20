#!/usr/bin/env python3
"""
Fixed WNBA Scraper - Uses actual player URLs from team rosters.
"""

import os
import pandas as pd
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

class FixedWNBAScraper:
    """
    Fixed WNBA scraper that extracts real player URLs from team pages.
    """
    
    def __init__(self, output_path: str = "data/wnba_current_gamelogs.csv"):
        self.output_path = output_path
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        self.base_url = "https://www.basketball-reference.com"
    
    def get_team_players_with_urls(self, team_abbr: str) -> list:
        """
        Get players and their actual Basketball Reference URLs from team roster.
        """
        print(f"📋 Getting players for {team_abbr}...")
        
        try:
            url = f"https://www.basketball-reference.com/wnba/teams/{team_abbr}/2024.html"
            
            time.sleep(1.5)
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            players_with_urls = []
            
            # Look for roster table
            roster_table = soup.find('table', {'id': 'roster'})
            
            if roster_table:
                rows = roster_table.find('tbody').find_all('tr')
                for row in rows:
                    name_cell = row.find('td', {'data-stat': 'player'})
                    if name_cell:
                        name_link = name_cell.find('a')
                        if name_link and name_link.get('href'):
                            player_name = name_link.text.strip()
                            player_url = name_link.get('href')
                            players_with_urls.append({
                                'name': player_name,
                                'url': player_url
                            })
            
            if players_with_urls:
                print(f"  ✅ Found {len(players_with_urls)} players with URLs for {team_abbr}")
                # Show first few for verification
                for i, player in enumerate(players_with_urls[:3]):
                    print(f"    {i+1}. {player['name']} -> {player['url']}")
                return players_with_urls
            else:
                print(f"  ⚠️ No players found for {team_abbr}")
                return []
                
        except Exception as e:
            print(f"  ❌ Error getting players for {team_abbr}: {e}")
            return []
    
    def scrape_player_game_logs(self, player_name: str, player_url: str) -> pd.DataFrame:
        """
        Scrape game logs using the actual player URL from Basketball Reference.
        """
        try:
            # Construct full URL
            full_url = self.base_url + player_url
            
            print(f"  📊 Trying URL: {full_url}")
            
            time.sleep(2)  # Be respectful
            response = requests.get(full_url, headers=self.headers)
            
            if response.status_code != 200:
                print(f"    ❌ Status {response.status_code}")
                return pd.DataFrame()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for 2024 game log table - try different possible IDs
            possible_table_ids = [
                'pgl_basic',
                'pgl_basic_2024', 
                'gamelog',
                'stats'
            ]
            
            gamelog_table = None
            for table_id in possible_table_ids:
                gamelog_table = soup.find('table', {'id': table_id})
                if gamelog_table:
                    print(f"    ✅ Found table with ID: {table_id}")
                    break
            
            if not gamelog_table:
                # Try to find any table with game data
                all_tables = soup.find_all('table')
                print(f"    📊 Found {len(all_tables)} total tables on page")
                
                # Look for table headers that suggest game logs
                for i, table in enumerate(all_tables):
                    headers = table.find_all('th')
                    header_text = [th.text.strip().lower() for th in headers]
                    
                    if any(keyword in ' '.join(header_text) for keyword in ['date', 'pts', 'ast', 'reb', 'game']):
                        print(f"    ✅ Found potential game log table {i}: {header_text[:5]}")
                        gamelog_table = table
                        break
            
            if gamelog_table:
                return self.parse_game_log_table(gamelog_table, player_name)
            else:
                print(f"    ⚠️ No game log table found for {player_name}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"    ❌ Error scraping {player_name}: {e}")
            return pd.DataFrame()
    
    def parse_game_log_table(self, table, player_name: str) -> pd.DataFrame:
        """
        Parse a game log table and extract relevant stats.
        """
        try:
            rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')
            
            game_logs = []
            
            for row in rows:
                # Skip header rows
                if row.get('class') and 'thead' in str(row.get('class')):
                    continue
                
                cells = row.find_all(['td', 'th'])
                if len(cells) < 10:  # Minimum columns needed
                    continue
                
                try:
                    # Try to extract basic stats - be flexible with column positions
                    row_data = [cell.text.strip() for cell in cells]
                    
                    # Look for date column (usually first or second)
                    date_val = ""
                    for i, val in enumerate(row_data[:3]):
                        if any(month in val.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                            date_val = val
                            break
                    
                    if not date_val:
                        continue
                    
                    # Extract numeric stats (points, rebounds, assists)
                    numeric_values = []
                    for val in row_data:
                        if val.isdigit():
                            numeric_values.append(int(val))
                        elif val and '.' in val and val.replace('.', '').isdigit():
                            numeric_values.append(float(val))
                    
                    if len(numeric_values) >= 3:  # Need at least a few stats
                        game_data = {
                            'PLAYER_NAME': player_name,
                            'GAME_DATE': date_val,
                            'PTS': numeric_values[-1] if numeric_values else 0,  # Points usually last
                            'AST': numeric_values[-3] if len(numeric_values) >= 3 else 0,
                            'REB': numeric_values[-2] if len(numeric_values) >= 2 else 0,
                            'STL': 0,  # Will try to extract these later
                            'BLK': 0,
                            'TOV': 0,
                            'MIN': row_data[2] if len(row_data) > 2 else "0:00",
                            'FGM': numeric_values[0] if numeric_values else 0,
                            'FGA': numeric_values[1] if len(numeric_values) > 1 else 0,
                            'FG%': 0.0,
                            '3PM': 0,
                            '3PA': 0,
                            '3P%': 0.0,
                            'FTM': 0,
                            'FTA': 0,
                            'FT%': 0.0
                        }
                        game_logs.append(game_data)
                
                except (ValueError, IndexError):
                    continue
            
            if game_logs:
                print(f"    ✅ Parsed {len(game_logs)} games for {player_name}")
                return pd.DataFrame(game_logs)
            else:
                print(f"    ⚠️ No valid game data parsed for {player_name}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"    ❌ Error parsing table for {player_name}: {e}")
            return pd.DataFrame()
    
    def run_test_ingestion(self) -> bool:
        """
        Test ingestion with a limited set of players.
        """
        print("🏀 Starting Fixed WNBA Scraper Test...\n")
        
        # Test with just Indiana Fever (has Caitlin Clark)
        test_team = "IND"
        
        print(f"🔍 Testing with {test_team} (Indiana Fever)...")
        
        # Get players with their URLs
        players = self.get_team_players_with_urls(test_team)
        
        if not players:
            print("❌ No players found")
            return False
        
        all_game_logs = []
        
        # Test with first 3 players
        test_players = players[:3]
        
        for player in test_players:
            player_name = player['name']
            player_url = player['url']
            
            print(f"\n📊 Scraping {player_name}...")
            print(f"    URL: {player_url}")
            
            player_logs = self.scrape_player_game_logs(player_name, player_url)
            
            if not player_logs.empty:
                all_game_logs.append(player_logs)
                print(f"    ✅ SUCCESS: {len(player_logs)} games")
            else:
                print(f"    ❌ No data found")
        
        # Save results if any
        if all_game_logs:
            final_df = pd.concat(all_game_logs, ignore_index=True)
            final_df = final_df.sort_values(['PLAYER_NAME', 'GAME_DATE'])
            
            final_df.to_csv(self.output_path, index=False)
            
            print(f"\n🎉 SUCCESS!")
            print(f"📊 Total games: {len(final_df)}")
            print(f"👥 Players: {final_df['PLAYER_NAME'].nunique()}")
            print(f"💾 Saved to: {self.output_path}")
            
            # Show sample
            print(f"\n📋 Sample data:")
            print(final_df[['PLAYER_NAME', 'GAME_DATE', 'PTS', 'AST', 'REB']].head())
            
            return True
        else:
            print("\n❌ No data collected")
            return False

def main():
    """Test the fixed scraper."""
    scraper = FixedWNBAScraper()
    success = scraper.run_test_ingestion()
    
    if success:
        print("\n✅ Fixed scraper working!")
        print("🔄 Ready to expand to more teams and players!")
    else:
        print("\n❌ Still having issues - may need different approach")

if __name__ == "__main__":
    main()