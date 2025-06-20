#!/usr/bin/env python3
"""
FINAL Working WNBA Scraper - Uses exact table structure we discovered.
"""

import os
import pandas as pd
import time
import requests
from bs4 import BeautifulSoup

class FinalWNBAScraper:
    """
    Working WNBA scraper that targets the exact table structure found on Basketball Reference.
    """
    
    def __init__(self, output_path: str = "data/wnba_current_gamelogs.csv"):
        self.output_path = output_path
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        self.base_url = "https://www.basketball-reference.com"
    
    def get_team_players_with_urls(self, team_abbr: str) -> list:
        """Get players and their URLs from team roster."""
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
                print(f"  ✅ Found {len(players_with_urls)} players for {team_abbr}")
                return players_with_urls
            else:
                print(f"  ⚠️ No players found for {team_abbr}")
                return []
                
        except Exception as e:
            print(f"  ❌ Error getting players for {team_abbr}: {e}")
            return []
    
    def scrape_player_game_logs(self, player_name: str, player_url: str) -> pd.DataFrame:
        """
        Scrape game logs using the exact table structure we discovered.
        Target: Table ID 'last5' with known column positions.
        """
        try:
            full_url = self.base_url + player_url
            print(f"  📊 Scraping {player_name}: {full_url}")
            
            time.sleep(2)
            response = requests.get(full_url, headers=self.headers)
            
            if response.status_code != 200:
                print(f"    ❌ Status {response.status_code}")
                return pd.DataFrame()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Target the exact table we found: ID = "last5"
            game_table = soup.find('table', {'id': 'last5'})
            
            if game_table:
                print(f"    ✅ Found 'last5' table")
                return self.parse_last5_table(game_table, player_name)
            else:
                print(f"    ❌ No 'last5' table found")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"    ❌ Error scraping {player_name}: {e}")
            return pd.DataFrame()
    
    def parse_last5_table(self, table, player_name: str) -> pd.DataFrame:
        """
        Parse the 'last5' table using exact column positions we discovered.
        
        Expected headers (from debug):
        ['Date', 'Team', '', 'Opp', 'Result', 'GS', 'MP', 'FG', 'FGA', 'FG%', 
         '3P', '3PA', '3P%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 
         'STL', 'BLK', 'TOV', 'PF', 'PTS', 'GmSc', '+/-']
         
        Key column indices:
        0=Date, 6=MP, 7=FG, 8=FGA, 9=FG%, 10=3P, 11=3PA, 12=3P%, 
        13=FT, 14=FTA, 15=FT%, 18=TRB, 19=AST, 20=STL, 21=BLK, 22=TOV, 24=PTS
        """
        try:
            # Get data rows (skip header)
            rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')[1:]
            
            game_logs = []
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                # Need at least 25 columns for all our data
                if len(cells) < 25:
                    continue
                
                try:
                    # Extract text from each cell
                    cell_data = [cell.text.strip() for cell in cells]
                    
                    # Skip empty rows or header repeats
                    if not cell_data[0] or cell_data[0].lower() in ['date', '']:
                        continue
                    
                    # Helper function to safely convert to number
                    def safe_convert(value, default=0, as_float=False):
                        try:
                            if value == '' or value == '-':
                                return default
                            return float(value) if as_float else int(value)
                        except:
                            return default
                    
                    # Map to our standard format using exact column positions
                    game_data = {
                        'PLAYER_NAME': player_name,
                        'GAME_DATE': cell_data[0],  # Column 0: Date
                        'PTS': safe_convert(cell_data[24]),  # Column 24: PTS
                        'AST': safe_convert(cell_data[19]),  # Column 19: AST  
                        'REB': safe_convert(cell_data[18]),  # Column 18: TRB (Total Rebounds)
                        'STL': safe_convert(cell_data[20]),  # Column 20: STL
                        'BLK': safe_convert(cell_data[21]),  # Column 21: BLK
                        'TOV': safe_convert(cell_data[22]),  # Column 22: TOV
                        'MIN': cell_data[6],  # Column 6: MP (Minutes)
                        'FGM': safe_convert(cell_data[7]),   # Column 7: FG
                        'FGA': safe_convert(cell_data[8]),   # Column 8: FGA
                        'FG%': safe_convert(cell_data[9], as_float=True),   # Column 9: FG%
                        '3PM': safe_convert(cell_data[10]),  # Column 10: 3P
                        '3PA': safe_convert(cell_data[11]),  # Column 11: 3PA
                        '3P%': safe_convert(cell_data[12], as_float=True),  # Column 12: 3P%
                        'FTM': safe_convert(cell_data[13]),  # Column 13: FT
                        'FTA': safe_convert(cell_data[14]),  # Column 14: FTA
                        'FT%': safe_convert(cell_data[15], as_float=True)   # Column 15: FT%
                    }
                    
                    game_logs.append(game_data)
                    
                except (ValueError, IndexError) as e:
                    print(f"    ⚠️ Skipping malformed row: {e}")
                    continue
            
            if game_logs:
                print(f"    ✅ Successfully parsed {len(game_logs)} games for {player_name}")
                return pd.DataFrame(game_logs)
            else:
                print(f"    ⚠️ No valid games parsed for {player_name}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"    ❌ Error parsing table for {player_name}: {e}")
            return pd.DataFrame()
    
    def run_focused_test(self) -> bool:
        """
        Test with Indiana Fever players (we know Caitlin Clark works).
        """
        print("🏀 Final WNBA Scraper - Focused Test\n")
        
        # Test with Indiana Fever
        test_team = "IND"
        
        # Get players
        players = self.get_team_players_with_urls(test_team)
        
        if not players:
            print("❌ No players found")
            return False
        
        all_game_logs = []
        
        # Test with first 3 players (including Caitlin Clark)
        test_players = players[:3]
        
        for player in test_players:
            player_name = player['name']
            player_url = player['url']
            
            print(f"\n📊 Processing {player_name}...")
            
            player_logs = self.scrape_player_game_logs(player_name, player_url)
            
            if not player_logs.empty:
                all_game_logs.append(player_logs)
                print(f"    🎉 SUCCESS: {len(player_logs)} games collected!")
                
                # Show sample data
                sample = player_logs.head(3)
                print(f"    📋 Sample games:")
                for _, game in sample.iterrows():
                    print(f"      {game['GAME_DATE']}: {game['PTS']} pts, {game['AST']} ast, {game['REB']} reb")
            else:
                print(f"    ❌ No data collected for {player_name}")
        
        # Save results
        if all_game_logs:
            final_df = pd.concat(all_game_logs, ignore_index=True)
            final_df = final_df.sort_values(['PLAYER_NAME', 'GAME_DATE'])
            
            final_df.to_csv(self.output_path, index=False)
            
            print(f"\n🎉 FINAL SUCCESS!")
            print(f"📊 Total games collected: {len(final_df)}")
            print(f"👥 Players: {final_df['PLAYER_NAME'].nunique()}")
            print(f"📅 Date range: {final_df['GAME_DATE'].min()} to {final_df['GAME_DATE'].max()}")
            print(f"💾 Saved to: {self.output_path}")
            
            # Show summary stats
            print(f"\n📋 Player Summary:")
            for player in final_df['PLAYER_NAME'].unique():
                player_data = final_df[final_df['PLAYER_NAME'] == player]
                avg_pts = player_data['PTS'].mean()
                print(f"  - {player}: {len(player_data)} games, {avg_pts:.1f} ppg avg")
            
            return True
        else:
            print("\n❌ No data collected from any players")
            return False

def main():
    """Run the final working scraper."""
    scraper = FinalWNBAScraper()
    success = scraper.run_focused_test()
    
    if success:
        print("\n🎉 BREAKTHROUGH! WNBA data scraping is now working!")
        print("🔄 Ready to integrate with your prediction pipeline!")
    else:
        print("\n❌ Still having issues")

if __name__ == "__main__":
    main()