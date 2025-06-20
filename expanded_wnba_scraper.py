#!/usr/bin/env python3
"""
Expanded WNBA Scraper - Full League Coverage
==========================================

Scrapes game logs for all WNBA teams and players for comprehensive coverage.

Usage:
    python expanded_wnba_scraper.py [--teams all] [--players-per-team 8] [--output data/wnba_full_gamelogs.csv]
"""

import os
import sys
import pandas as pd
import time
import requests
from bs4 import BeautifulSoup
import argparse
from datetime import datetime

class ExpandedWNBAScraper:
    """
    Comprehensive WNBA scraper for all teams and players.
    """
    
    def __init__(self, output_path: str = "data/wnba_full_gamelogs.csv", 
                 max_players_per_team: int = 8, teams: str = "all"):
        self.output_path = output_path
        self.max_players_per_team = max_players_per_team
        self.target_teams = teams
        
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        self.base_url = "https://www.basketball-reference.com"
        
        # All 12 WNBA teams
        self.all_teams = {
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
        
        # Statistics tracking
        self.stats = {
            'teams_processed': 0,
            'players_found': 0,
            'players_with_data': 0,
            'total_games': 0,
            'start_time': datetime.now()
        }
    
    def log_progress(self, message: str, level: str = "INFO"):
        """Enhanced logging with timestamps."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "SUCCESS":
            print(f"[{timestamp}] ✅ {message}")
        elif level == "ERROR":
            print(f"[{timestamp}] ❌ {message}")
        elif level == "WARNING":
            print(f"[{timestamp}] ⚠️  {message}")
        else:
            print(f"[{timestamp}] 📊 {message}")
    
    def get_team_players_with_urls(self, team_abbr: str) -> list:
        """Get players and their URLs from team roster."""
        self.log_progress(f"Getting roster for {team_abbr} ({self.all_teams.get(team_abbr, team_abbr)})...")
        
        try:
            url = f"https://www.basketball-reference.com/wnba/teams/{team_abbr}/2024.html"
            
            time.sleep(1.5)  # Respectful rate limiting
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
                                'url': player_url,
                                'team': team_abbr
                            })
            
            # Limit players per team if specified
            if self.max_players_per_team > 0:
                players_with_urls = players_with_urls[:self.max_players_per_team]
            
            if players_with_urls:
                self.log_progress(f"Found {len(players_with_urls)} players for {team_abbr}", "SUCCESS")
                self.stats['players_found'] += len(players_with_urls)
                return players_with_urls
            else:
                self.log_progress(f"No players found for {team_abbr}", "WARNING")
                return []
                
        except Exception as e:
            self.log_progress(f"Error getting players for {team_abbr}: {e}", "ERROR")
            return []
    
    def scrape_player_game_logs(self, player_name: str, player_url: str, team: str) -> pd.DataFrame:
        """Scrape game logs for a specific player."""
        try:
            full_url = self.base_url + player_url
            
            time.sleep(2)  # Respectful rate limiting
            response = requests.get(full_url, headers=self.headers)
            
            if response.status_code != 200:
                self.log_progress(f"Bad response for {player_name}: {response.status_code}", "WARNING")
                return pd.DataFrame()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Target the 'last5' table (recent games)
            game_table = soup.find('table', {'id': 'last5'})
            
            if game_table:
                df = self.parse_last5_table(game_table, player_name, team)
                if not df.empty:
                    self.stats['players_with_data'] += 1
                    self.stats['total_games'] += len(df)
                    self.log_progress(f"{player_name}: {len(df)} games", "SUCCESS")
                return df
            else:
                self.log_progress(f"{player_name}: No recent games table found", "WARNING")
                return pd.DataFrame()
                
        except Exception as e:
            self.log_progress(f"Error scraping {player_name}: {e}", "ERROR")
            return pd.DataFrame()
    
    def parse_last5_table(self, table, player_name: str, team: str) -> pd.DataFrame:
        """Parse the 'last5' table with enhanced error handling."""
        try:
            rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')[1:]
            
            game_logs = []
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) < 25:
                    continue
                
                try:
                    cell_data = [cell.text.strip() for cell in cells]
                    
                    # Skip empty rows or headers
                    if not cell_data[0] or cell_data[0].lower() in ['date', '']:
                        continue
                    
                    def safe_convert(value, default=0, as_float=False):
                        try:
                            if value == '' or value == '-':
                                return default
                            return float(value) if as_float else int(value)
                        except:
                            return default
                    
                    # Enhanced game data with team info
                    game_data = {
                        'PLAYER_NAME': player_name,
                        'TEAM': team,
                        'GAME_DATE': cell_data[0],
                        'PTS': safe_convert(cell_data[24]),
                        'AST': safe_convert(cell_data[19]),
                        'REB': safe_convert(cell_data[18]),
                        'STL': safe_convert(cell_data[20]),
                        'BLK': safe_convert(cell_data[21]),
                        'TOV': safe_convert(cell_data[22]),
                        'MIN': cell_data[6],
                        'FGM': safe_convert(cell_data[7]),
                        'FGA': safe_convert(cell_data[8]),
                        'FG%': safe_convert(cell_data[9], as_float=True),
                        '3PM': safe_convert(cell_data[10]),
                        '3PA': safe_convert(cell_data[11]),
                        '3P%': safe_convert(cell_data[12], as_float=True),
                        'FTM': safe_convert(cell_data[13]),
                        'FTA': safe_convert(cell_data[14]),
                        'FT%': safe_convert(cell_data[15], as_float=True)
                    }
                    
                    game_logs.append(game_data)
                    
                except (ValueError, IndexError):
                    continue
            
            return pd.DataFrame(game_logs) if game_logs else pd.DataFrame()
                
        except Exception as e:
            self.log_progress(f"Error parsing table for {player_name}: {e}", "ERROR")
            return pd.DataFrame()
    
    def get_teams_to_process(self) -> list:
        """Determine which teams to process based on configuration."""
        if self.target_teams == "all":
            return list(self.all_teams.keys())
        elif self.target_teams == "top":
            # Top teams by popularity/performance
            return ['IND', 'LV', 'NY', 'SEA', 'CONN', 'MIN']
        elif isinstance(self.target_teams, str):
            # Single team
            return [self.target_teams.upper()]
        else:
            # List of teams
            return [team.upper() for team in self.target_teams]
    
    def run_full_ingestion(self) -> bool:
        """
        Run comprehensive WNBA data ingestion.
        """
        self.log_progress("🏀 Starting Expanded WNBA Scraper")
        self.log_progress(f"Target: {self.target_teams} teams, max {self.max_players_per_team} players per team")
        
        teams_to_process = self.get_teams_to_process()
        all_game_logs = []
        
        self.log_progress(f"Processing {len(teams_to_process)} teams: {', '.join(teams_to_process)}")
        
        for i, team in enumerate(teams_to_process):
            self.log_progress(f"\n{'='*50}")
            self.log_progress(f"TEAM {i+1}/{len(teams_to_process)}: {team} ({self.all_teams.get(team, team)})")
            self.log_progress(f"{'='*50}")
            
            # Get players for this team
            players = self.get_team_players_with_urls(team)
            
            if not players:
                self.log_progress(f"Skipping {team} - no players found", "WARNING")
                continue
            
            self.stats['teams_processed'] += 1
            
            # Process each player
            for j, player in enumerate(players):
                player_name = player['name']
                player_url = player['url']
                
                self.log_progress(f"  Player {j+1}/{len(players)}: {player_name}")
                
                player_logs = self.scrape_player_game_logs(player_name, player_url, team)
                
                if not player_logs.empty:
                    all_game_logs.append(player_logs)
                
                # Progress update every 10 players
                if (j + 1) % 10 == 0:
                    elapsed = datetime.now() - self.stats['start_time']
                    self.log_progress(f"Progress: {self.stats['players_with_data']} players with data, {self.stats['total_games']} total games ({elapsed})")
        
        # Save results
        if all_game_logs:
            final_df = pd.concat(all_game_logs, ignore_index=True)
            final_df = final_df.sort_values(['TEAM', 'PLAYER_NAME', 'GAME_DATE'])
            
            final_df.to_csv(self.output_path, index=False)
            
            self.log_success_summary(final_df)
            return True
        else:
            self.log_progress("No data collected from any players", "ERROR")
            return False
    
    def log_success_summary(self, df: pd.DataFrame):
        """Log comprehensive success summary."""
        elapsed = datetime.now() - self.stats['start_time']
        
        self.log_progress("\n" + "="*60)
        self.log_progress("🎉 EXPANDED WNBA SCRAPER - FINAL RESULTS", "SUCCESS")
        self.log_progress("="*60)
        
        self.log_progress(f"📊 Total games collected: {len(df)}")
        self.log_progress(f"👥 Unique players: {df['PLAYER_NAME'].nunique()}")
        self.log_progress(f"🏀 Teams represented: {df['TEAM'].nunique()}")
        self.log_progress(f"📅 Date range: {df['GAME_DATE'].min()} to {df['GAME_DATE'].max()}")
        self.log_progress(f"⏱️ Total time: {elapsed}")
        self.log_progress(f"💾 Saved to: {self.output_path}")
        
        # Team breakdown
        self.log_progress("\n📋 Team Breakdown:")
        team_summary = df.groupby('TEAM').agg({
            'PLAYER_NAME': 'nunique',
            'PTS': 'count'
        }).round(1)
        team_summary.columns = ['Players', 'Games']
        
        for team, row in team_summary.iterrows():
            team_name = self.all_teams.get(team, team)
            self.log_progress(f"  {team} ({team_name}): {int(row['Players'])} players, {int(row['Games'])} games")
        
        # Top performers
        self.log_progress("\n🌟 Top Performers (by PPG):")
        top_scorers = df.groupby('PLAYER_NAME')['PTS'].mean().sort_values(ascending=False).head(10)
        for player, ppg in top_scorers.items():
            player_team = df[df['PLAYER_NAME'] == player]['TEAM'].iloc[0]
            self.log_progress(f"  {player} ({player_team}): {ppg:.1f} ppg")
        
        self.log_progress("\n🚀 Ready for integration with prediction pipeline!", "SUCCESS")

def main():
    """CLI entry point with configuration options."""
    parser = argparse.ArgumentParser(description='Expanded WNBA Data Scraper')
    parser.add_argument('--teams', default='all', 
                       help='Teams to scrape: "all", "top", or specific team like "IND"')
    parser.add_argument('--players-per-team', type=int, default=8,
                       help='Maximum players per team to scrape (0 = all)')
    parser.add_argument('--output', default='data/wnba_full_gamelogs.csv',
                       help='Output CSV file path')
    
    args = parser.parse_args()
    
    scraper = ExpandedWNBAScraper(
        output_path=args.output,
        max_players_per_team=args.players_per_team,
        teams=args.teams
    )
    
    success = scraper.run_full_ingestion()
    
    if success:
        print(f"\n✅ SUCCESS! Expanded WNBA data saved to {args.output}")
        print("🔄 Ready to feed into your prediction system!")
    else:
        print(f"\n❌ Failed to collect data")
        sys.exit(1)

if __name__ == "__main__":
    main()