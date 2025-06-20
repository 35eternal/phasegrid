#!/usr/bin/env python3
"""
WNBA Data Ingestion using Basketball Reference Scraper
=====================================================

Uses basketball-reference-scraper to get real WNBA data.

Requirements:
    pip install basketball-reference-scraper pandas requests beautifulsoup4
"""

import os
import pandas as pd
import time
from datetime import datetime
from typing import Optional, List, Dict

try:
    # Try the official basketball_reference_scraper
    from basketball_reference_scraper.seasons import get_schedule, get_standings
    from basketball_reference_scraper.players import get_game_logs, get_player_headshot
    from basketball_reference_scraper.teams import get_roster, get_team_stats
    BR_SCRAPER_AVAILABLE = True
except ImportError:
    print("basketball_reference_scraper not found. Install with: pip install basketball-reference-scraper")
    BR_SCRAPER_AVAILABLE = False

import requests
from bs4 import BeautifulSoup

class WNBABasketballRefScraper:
    """
    WNBA data scraper using Basketball Reference.
    """
    
    def __init__(self, output_path: str = "data/wnba_current_gamelogs.csv"):
        self.output_path = output_path
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        
        # WNBA team abbreviations
        self.wnba_teams = {
            'ATL': 'Atlanta Dream',
            'CHI': 'Chicago Sky', 
            'CONN': 'Connecticut Sun',
            'DAL': 'Dallas Wings',
            'IND': 'Indiana Fever',
            'LV': 'Las Vegas Aces',
            'MIN': 'Minnesota Lynx',
            'NY': 'New York Liberty',
            'PHX': 'Phoenix Mercury',
            'SEA': 'Seattle Storm',
            'WAS': 'Washington Mystics',
            'LA': 'Los Angeles Sparks'
        }
        
        # Known WNBA players for testing
        self.known_players = [
            "A'ja Wilson", "Breanna Stewart", "Diana Taurasi", 
            "Sabrina Ionescu", "Kelsey Plum", "Jackie Young",
            "Caitlin Clark", "Angel Reese", "Napheesa Collier",
            "Jewell Loyd", "Alyssa Thomas", "Jonquel Jones"
        ]
    
    def get_wnba_schedule_2024(self) -> pd.DataFrame:
        """
        Scrape WNBA schedule directly from Basketball Reference.
        """
        print("🔍 Fetching WNBA 2024 schedule...")
        
        try:
            if BR_SCRAPER_AVAILABLE:
                # Try using the official scraper first
                schedule = get_schedule(2024, league="WNBA")
                return schedule
        except Exception as e:
            print(f"Official scraper failed: {e}")
        
        # Fallback: Direct scraping
        try:
            url = "https://www.basketball-reference.com/wnba/years/2024_games.html"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            time.sleep(1)  # Be respectful
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the games table
            games_table = soup.find('table', {'id': 'schedule'})
            if not games_table:
                print("❌ Could not find games table")
                return pd.DataFrame()
            
            # Parse table
            rows = games_table.find('tbody').find_all('tr')
            games = []
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 7:  # Basic validation
                    game_data = {
                        'Date': cells[0].text.strip(),
                        'Home': cells[2].text.strip() if len(cells) > 2 else '',
                        'Away': cells[4].text.strip() if len(cells) > 4 else '',
                        'Home_Score': cells[3].text.strip() if len(cells) > 3 else '',
                        'Away_Score': cells[5].text.strip() if len(cells) > 5 else ''
                    }
                    games.append(game_data)
            
            if games:
                print(f"✅ Found {len(games)} games from schedule")
                return pd.DataFrame(games)
            else:
                print("❌ No games found in schedule")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Schedule scraping failed: {e}")
            return pd.DataFrame()
    
    def get_wnba_teams_2024(self) -> List[str]:
        """
        Get list of WNBA teams that played in 2024.
        """
        print("🔍 Getting WNBA teams...")
        
        try:
            # Try Basketball Reference teams page
            url = "https://www.basketball-reference.com/wnba/years/2024.html"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            time.sleep(1)
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for team links
            team_links = soup.find_all('a', href=lambda x: x and '/wnba/teams/' in x and '/2024.html' in x)
            teams = []
            
            for link in team_links:
                team_abbr = link['href'].split('/teams/')[1].split('/')[0].upper()
                if team_abbr in self.wnba_teams:
                    teams.append(team_abbr)
            
            if teams:
                print(f"✅ Found {len(teams)} WNBA teams: {', '.join(teams)}")
                return list(set(teams))  # Remove duplicates
            else:
                print("⚠️ No teams found, using default list")
                return list(self.wnba_teams.keys())
                
        except Exception as e:
            print(f"❌ Team fetching failed: {e}, using default list")
            return list(self.wnba_teams.keys())
    
    def get_team_players_2024(self, team_abbr: str) -> List[str]:
        """
        Get players for a specific WNBA team in 2024.
        """
        print(f"📋 Getting players for {team_abbr}...")
        
        try:
            url = f"https://www.basketball-reference.com/wnba/teams/{team_abbr}/2024.html"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            time.sleep(1.5)  # Be extra respectful to avoid rate limits
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for roster table
            roster_table = soup.find('table', {'id': 'roster'})
            players = []
            
            if roster_table:
                rows = roster_table.find('tbody').find_all('tr')
                for row in rows:
                    name_cell = row.find('td', {'data-stat': 'player'})
                    if name_cell:
                        # Extract player name from link
                        name_link = name_cell.find('a')
                        if name_link:
                            player_name = name_link.text.strip()
                            players.append(player_name)
            
            if players:
                print(f"  ✅ Found {len(players)} players for {team_abbr}")
                return players
            else:
                print(f"  ⚠️ No players found for {team_abbr}")
                return []
                
        except Exception as e:
            print(f"  ❌ Error getting players for {team_abbr}: {e}")
            return []
    
    def scrape_player_game_logs_2024(self, player_name: str) -> pd.DataFrame:
        """
        Scrape game logs for a specific player.
        """
        try:
            # Format player name for URL
            name_parts = player_name.lower().replace("'", "").replace(".", "").split()
            if len(name_parts) >= 2:
                # Basketball Reference naming convention
                last_name = name_parts[-1]
                first_name = name_parts[0]
                
                # Create player ID (first 5 letters of last name + first 2 of first name + 01)
                player_id = (last_name[:5] + first_name[:2] + "01").lower()
                
                url = f"https://www.basketball-reference.com/wnba/players/{last_name[0]}/{player_id}/gamelog/2024"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                time.sleep(2)  # Respectful delay
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for game log table
                    gamelog_table = soup.find('table', {'id': 'pgl_basic'})
                    
                    if gamelog_table:
                        # Parse the table
                        rows = gamelog_table.find('tbody').find_all('tr')
                        game_logs = []
                        
                        for row in rows:
                            if row.get('class') and 'thead' in row.get('class'):
                                continue  # Skip header rows
                            
                            cells = row.find_all('td')
                            if len(cells) >= 20:  # Ensure we have enough columns
                                try:
                                    game_data = {
                                        'PLAYER_NAME': player_name,
                                        'GAME_DATE': cells[1].text.strip(),
                                        'PTS': int(cells[28].text.strip()) if cells[28].text.strip().isdigit() else 0,
                                        'AST': int(cells[21].text.strip()) if cells[21].text.strip().isdigit() else 0,
                                        'REB': int(cells[18].text.strip()) if cells[18].text.strip().isdigit() else 0,
                                        'STL': int(cells[22].text.strip()) if cells[22].text.strip().isdigit() else 0,
                                        'BLK': int(cells[23].text.strip()) if cells[23].text.strip().isdigit() else 0,
                                        'TOV': int(cells[24].text.strip()) if cells[24].text.strip().isdigit() else 0,
                                        'MIN': cells[7].text.strip(),
                                        'FGM': int(cells[8].text.strip()) if cells[8].text.strip().isdigit() else 0,
                                        'FGA': int(cells[9].text.strip()) if cells[9].text.strip().isdigit() else 0,
                                        'FG%': float(cells[10].text.strip()) if cells[10].text.strip() and cells[10].text.strip() != '' else 0.0,
                                        '3PM': int(cells[11].text.strip()) if cells[11].text.strip().isdigit() else 0,
                                        '3PA': int(cells[12].text.strip()) if cells[12].text.strip().isdigit() else 0,
                                        '3P%': float(cells[13].text.strip()) if cells[13].text.strip() and cells[13].text.strip() != '' else 0.0,
                                        'FTM': int(cells[14].text.strip()) if cells[14].text.strip().isdigit() else 0,
                                        'FTA': int(cells[15].text.strip()) if cells[15].text.strip().isdigit() else 0,
                                        'FT%': float(cells[16].text.strip()) if cells[16].text.strip() and cells[16].text.strip() != '' else 0.0
                                    }
                                    game_logs.append(game_data)
                                except (ValueError, IndexError):
                                    continue  # Skip malformed rows
                        
                        if game_logs:
                            print(f"  ✅ Found {len(game_logs)} games for {player_name}")
                            return pd.DataFrame(game_logs)
            
            print(f"  ⚠️ No game logs found for {player_name}")
            return pd.DataFrame()
            
        except Exception as e:
            print(f"  ❌ Error scraping {player_name}: {e}")
            return pd.DataFrame()
    
    def run_ingestion(self) -> bool:
        """
        Main ingestion process.
        """
        print("🏀 Starting WNBA Basketball Reference Scraping...\n")
        
        all_game_logs = []
        
        # Get WNBA teams
        teams = self.get_wnba_teams_2024()
        
        # For initial testing, limit to a few teams and players
        test_teams = teams[:3]  # First 3 teams to avoid overwhelming
        print(f"📝 Testing with teams: {test_teams}")
        
        for team in test_teams:
            print(f"\n🔍 Processing {team} ({self.wnba_teams.get(team, team)})...")
            
            # Get players for this team
            players = self.get_team_players_2024(team)
            
            # Limit to first few players per team for testing
            test_players = players[:3]
            
            for player in test_players:
                print(f"  📊 Scraping {player}...")
                
                player_logs = self.scrape_player_game_logs_2024(player)
                
                if not player_logs.empty:
                    all_game_logs.append(player_logs)
        
        # Combine all results
        if all_game_logs:
            final_df = pd.concat(all_game_logs, ignore_index=True)
            final_df = final_df.sort_values(['PLAYER_NAME', 'GAME_DATE'])
            
            # Save to CSV
            final_df.to_csv(self.output_path, index=False)
            
            print(f"\n🎉 SUCCESS!")
            print(f"📊 Total games: {len(final_df)}")
            print(f"👥 Unique players: {final_df['PLAYER_NAME'].nunique()}")
            print(f"📅 Date range: {final_df['GAME_DATE'].min()} to {final_df['GAME_DATE'].max()}")
            print(f"💾 Saved to: {self.output_path}")
            
            # Show sample
            print(f"\n📋 Sample data:")
            print(final_df[['PLAYER_NAME', 'GAME_DATE', 'PTS', 'AST', 'REB']].head(10))
            
            return True
        else:
            print("\n❌ No data found")
            return False

def main():
    """CLI entry point."""
    scraper = WNBABasketballRefScraper()
    success = scraper.run_ingestion()
    
    if success:
        print("\n✅ WNBA data ingestion completed!")
        print("🔄 Ready for integration with your prediction pipeline!")
    else:
        print("\n❌ Ingestion failed - check output above for details")

if __name__ == "__main__":
    main()