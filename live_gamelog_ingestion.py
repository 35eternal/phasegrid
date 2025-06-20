"""
Live WNBA Game Log Ingestion System
Fetches current 2025 WNBA game logs from NBA Stats API
Formats data to match existing analysis pipeline requirements
"""

import requests
import pandas as pd
import time
import logging
from datetime import datetime, timedelta
import os
from pathlib import Path
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('live_ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WNBALiveIngestion:
    def __init__(self):
        self.base_url = "https://stats.nba.com/stats"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.wnba.com/',
            'x-nba-stats-origin': 'stats',
            'x-nba-stats-token': 'true'
        }
        
        # Ensure data directory exists
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Rate limiting
        self.request_delay = 0.6  # 600ms between requests
        
    def make_api_request(self, endpoint, params=None):
        """Make API request with proper rate limiting and error handling"""
        try:
            time.sleep(self.request_delay)
            
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning("Rate limited. Waiting 5 seconds...")
                time.sleep(5)
                return self.make_api_request(endpoint, params)
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {str(e)}")
            return None
    
    def get_wnba_teams(self):
        """Get list of WNBA teams for current season"""
        logger.info("Fetching WNBA teams...")
        
        # Use leagueteams endpoint specifically for WNBA
        params = {
            'LeagueID': '10',  # WNBA
            'Season': '2025'
        }
        
        data = self.make_api_request('leagueteams', params)
        if not data:
            logger.error("Failed to fetch WNBA teams")
            return []
            
        try:
            teams = []
            result_set = data['resultSets'][0]
            headers = result_set['headers']
            rows = result_set['rowSet']
            
            team_id_idx = headers.index('TEAM_ID')
            team_name_idx = headers.index('TEAM_NAME')
            
            for row in rows:
                teams.append({
                    'team_id': row[team_id_idx],
                    'team_name': row[team_name_idx]
                })
                
            logger.info(f"Found {len(teams)} WNBA teams")
            return teams
            
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error parsing teams data: {str(e)}")
            
            # Fallback: Use hardcoded 2025 WNBA teams if API fails
            logger.info("Using fallback WNBA team list...")
            fallback_teams = [
                {'team_id': 1611661313, 'team_name': 'Atlanta Dream'},
                {'team_id': 1611661314, 'team_name': 'Chicago Sky'},
                {'team_id': 1611661315, 'team_name': 'Connecticut Sun'},
                {'team_id': 1611661316, 'team_name': 'Dallas Wings'},
                {'team_id': 1611661317, 'team_name': 'Indiana Fever'},
                {'team_id': 1611661318, 'team_name': 'Las Vegas Aces'},
                {'team_id': 1611661319, 'team_name': 'Minnesota Lynx'},
                {'team_id': 1611661320, 'team_name': 'New York Liberty'},
                {'team_id': 1611661321, 'team_name': 'Phoenix Mercury'},
                {'team_id': 1611661322, 'team_name': 'Seattle Storm'},
                {'team_id': 1611661323, 'team_name': 'Washington Mystics'},
                {'team_id': 1611661324, 'team_name': 'Golden State Valkyries'}  # New expansion team
            ]
            return fallback_teams
    
    def get_team_roster(self, team_id):
        """Get roster for a specific team"""
        logger.info(f"Fetching roster for team {team_id}...")
        
        params = {
            'TeamID': team_id,
            'Season': '2025'
        }
        
        data = self.make_api_request('commonteamroster', params)
        if not data:
            return []
            
        try:
            players = []
            result_set = data['resultSets'][0]
            headers = result_set['headers']
            rows = result_set['rowSet']
            
            player_id_idx = headers.index('PLAYER_ID')
            player_name_idx = headers.index('PLAYER')
            
            for row in rows:
                players.append({
                    'player_id': row[player_id_idx],
                    'player_name': row[player_name_idx]
                })
                
            return players
            
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error parsing roster data for team {team_id}: {str(e)}")
            return []
    
    def get_player_game_logs(self, player_id, player_name):
        """Get game logs for a specific player matching exact wnba_2024_gamelogs.csv format"""
        logger.info(f"Fetching game logs for {player_name} (ID: {player_id})")
        
        params = {
            'PlayerID': player_id,
            'Season': '2025',
            'SeasonType': 'Regular Season',
            'LeagueID': '10'  # WNBA
        }
        
        data = self.make_api_request('playergamelog', params)
        if not data:
            return []
            
        try:
            game_logs = []
            result_set = data['resultSets'][0]
            headers = result_set['headers']
            rows = result_set['rowSet']
            
            # Map column indices
            col_mapping = {header: idx for idx, header in enumerate(headers)}
            
            for row in rows:
                try:
                    # Convert minutes from "MM:SS" format to decimal if needed
                    minutes_raw = row[col_mapping.get('MIN', 0)] or 0
                    minutes_decimal = minutes_raw
                    minutes_sec = f"{minutes_raw}"  # Keep original format for MIN_SEC
                    
                    if isinstance(minutes_raw, str) and ':' in str(minutes_raw):
                        try:
                            min_parts = str(minutes_raw).split(':')
                            minutes_decimal = float(min_parts[0]) + float(min_parts[1]) / 60.0
                        except:
                            minutes_decimal = 0
                    
                    # Calculate percentages with error handling
                    def safe_pct(made, attempted):
                        try:
                            return round(made / attempted, 3) if attempted and attempted > 0 else 0.0
                        except:
                            return 0.0
                    
                    fgm = row[col_mapping.get('FGM', 0)] or 0
                    fga = row[col_mapping.get('FGA', 0)] or 0
                    fg3m = row[col_mapping.get('FG3M', 0)] or 0
                    fg3a = row[col_mapping.get('FG3A', 0)] or 0
                    ftm = row[col_mapping.get('FTM', 0)] or 0
                    fta = row[col_mapping.get('FTA', 0)] or 0
                    
                    # Build complete game log matching wnba_2024_gamelogs.csv format
                    game_log = {
                        'SEASON_YEAR': 2025,
                        'PLAYER_ID': player_id,
                        'PLAYER_NAME': player_name,
                        'NICKNAME': '',  # Not available from API
                        'TEAM_ID': row[col_mapping.get('Team_ID', 0)] or 0,
                        'TEAM_ABBREVIATION': row[col_mapping.get('TEAM_ABBREVIATION', '')] or '',
                        'TEAM_NAME': '',  # Will be filled in later
                        'GAME_ID': row[col_mapping.get('Game_ID', '')] or '',
                        'GAME_DATE': row[col_mapping.get('GAME_DATE', '')] or '',
                        'MATCHUP': row[col_mapping.get('MATCHUP', '')] or '',
                        'WL': row[col_mapping.get('WL', '')] or '',
                        'MIN': minutes_decimal,
                        'FGM': fgm,
                        'FGA': fga,
                        'FG_PCT': safe_pct(fgm, fga),
                        'FG3M': fg3m,
                        'FG3A': fg3a,
                        'FG3_PCT': safe_pct(fg3m, fg3a),
                        'FTM': ftm,
                        'FTA': fta,
                        'FT_PCT': safe_pct(ftm, fta),
                        'OREB': row[col_mapping.get('OREB', 0)] or 0,
                        'DREB': row[col_mapping.get('DREB', 0)] or 0,
                        'REB': row[col_mapping.get('REB', 0)] or 0,
                        'AST': row[col_mapping.get('AST', 0)] or 0,
                        'TOV': row[col_mapping.get('TOV', 0)] or 0,
                        'STL': row[col_mapping.get('STL', 0)] or 0,
                        'BLK': row[col_mapping.get('BLK', 0)] or 0,
                        'BLKA': row[col_mapping.get('BLKA', 0)] or 0,
                        'PF': row[col_mapping.get('PF', 0)] or 0,
                        'PFD': row[col_mapping.get('PFD', 0)] or 0,
                        'PTS': row[col_mapping.get('PTS', 0)] or 0,
                        'PLUS_MINUS': row[col_mapping.get('PLUS_MINUS', 0)] or 0,
                        'NBA_FANTASY_PTS': row[col_mapping.get('NBA_FANTASY_PTS', 0)] or 0,
                        'DD2': row[col_mapping.get('DD2', 0)] or 0,
                        'TD3': row[col_mapping.get('TD3', 0)] or 0,
                        'WNBA_FANTASY_PTS': row[col_mapping.get('WNBA_FANTASY_PTS', 0)] or 0,
                        
                        # Ranking fields - will be null initially, filled by your existing pipeline
                        'GP_RANK': None,
                        'W_RANK': None,
                        'L_RANK': None,
                        'W_PCT_RANK': None,
                        'MIN_RANK': None,
                        'FGM_RANK': None,
                        'FGA_RANK': None,
                        'FG_PCT_RANK': None,
                        'FG3M_RANK': None,
                        'FG3A_RANK': None,
                        'FG3_PCT_RANK': None,
                        'FTM_RANK': None,
                        'FTA_RANK': None,
                        'FT_PCT_RANK': None,
                        'OREB_RANK': None,
                        'DREB_RANK': None,
                        'REB_RANK': None,
                        'AST_RANK': None,
                        'TOV_RANK': None,
                        'STL_RANK': None,
                        'BLK_RANK': None,
                        'BLKA_RANK': None,
                        'PF_RANK': None,
                        'PFD_RANK': None,
                        'PTS_RANK': None,
                        'PLUS_MINUS_RANK': None,
                        'NBA_FANTASY_PTS_RANK': None,
                        'DD2_RANK': None,
                        'TD3_RANK': None,
                        'WNBA_FANTASY_PTS_RANK': None,
                        'AVAILABLE_FLAG': 1,
                        'MIN_SEC': minutes_sec
                    }
                    
                    game_logs.append(game_log)
                    
                except (KeyError, IndexError, ValueError) as e:
                    logger.warning(f"Error parsing game log row for {player_name}: {str(e)}")
                    continue
                    
            logger.info(f"Retrieved {len(game_logs)} game logs for {player_name}")
            return game_logs
            
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error parsing game logs for {player_name}: {str(e)}")
            return []
    
    def run_full_ingestion(self):
        """Run complete ingestion process"""
        logger.info("Starting WNBA live game log ingestion...")
        
        # Get all teams
        teams = self.get_wnba_teams()
        if not teams:
            logger.error("No teams found. Aborting.")
            return False
        
        all_game_logs = []
        total_players = 0
        
        for team in teams:
            logger.info(f"Processing team: {team['team_name']}")
            
            # Get team roster
            players = self.get_team_roster(team['team_id'])
            total_players += len(players)
            
            for player in players:
                try:
                    # Get player game logs
                    game_logs = self.get_player_game_logs(
                        player['player_id'], 
                        player['player_name']
                    )
                    all_game_logs.extend(game_logs)
                    
                except Exception as e:
                    logger.error(f"Error processing player {player['player_name']}: {str(e)}")
                    continue
        
        # Convert to DataFrame and save
        if all_game_logs:
            df = pd.DataFrame(all_game_logs)
            
            # Clean and format data
            df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'], errors='coerce')
            df = df.sort_values(['PLAYER_ID', 'GAME_DATE'])
            
            # Ensure column order matches wnba_2024_gamelogs.csv exactly
            column_order = [
                'SEASON_YEAR', 'PLAYER_ID', 'PLAYER_NAME', 'NICKNAME', 'TEAM_ID', 
                'TEAM_ABBREVIATION', 'TEAM_NAME', 'GAME_ID', 'GAME_DATE', 'MATCHUP', 
                'WL', 'MIN', 'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 
                'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'REB', 'AST', 'TOV', 
                'STL', 'BLK', 'BLKA', 'PF', 'PFD', 'PTS', 'PLUS_MINUS', 
                'NBA_FANTASY_PTS', 'DD2', 'TD3', 'WNBA_FANTASY_PTS', 'GP_RANK', 
                'W_RANK', 'L_RANK', 'W_PCT_RANK', 'MIN_RANK', 'FGM_RANK', 
                'FGA_RANK', 'FG_PCT_RANK', 'FG3M_RANK', 'FG3A_RANK', 'FG3_PCT_RANK', 
                'FTM_RANK', 'FTA_RANK', 'FT_PCT_RANK', 'OREB_RANK', 'DREB_RANK', 
                'REB_RANK', 'AST_RANK', 'TOV_RANK', 'STL_RANK', 'BLK_RANK', 
                'BLKA_RANK', 'PF_RANK', 'PFD_RANK', 'PTS_RANK', 'PLUS_MINUS_RANK', 
                'NBA_FANTASY_PTS_RANK', 'DD2_RANK', 'TD3_RANK', 'WNBA_FANTASY_PTS_RANK', 
                'AVAILABLE_FLAG', 'MIN_SEC'
            ]
            
            df = df[column_order]
            
            # Save to CSV following your naming convention
            output_path = self.data_dir / "wnba_2025_gamelogs.csv"
            df.to_csv(output_path, index=False)
            
            logger.info(f"Successfully saved {len(df)} game logs from {total_players} players to {output_path}")
            logger.info(f"Date range: {df['GAME_DATE'].min()} to {df['GAME_DATE'].max()}")
            logger.info(f"Output format matches wnba_2024_gamelogs.csv with {len(column_order)} columns")
            
            return True
        else:
            logger.error("No game logs retrieved")
            return False

def main():
    """Main execution function"""
    ingestion = WNBALiveIngestion()
    
    try:
        success = ingestion.run_full_ingestion()
        
        if success:
            logger.info("Live ingestion completed successfully!")
        else:
            logger.error("Live ingestion failed!")
            
    except Exception as e:
        logger.error(f"Fatal error during ingestion: {str(e)}")

if __name__ == "__main__":
    main()