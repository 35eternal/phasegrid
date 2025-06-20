"""
Live WNBA Game Log Ingestion System
Multi-source approach: ESPN API primary, NBA API fallback
Fetches current 2025 WNBA game logs from reliable public sources
Formats data to match existing wnba_2024_gamelogs.csv requirements
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
        # ESPN API (Primary source - more reliable)
        self.espn_base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba"
        
        # NBA Stats API (Fallback)
        self.nba_base_url = "https://stats.nba.com/stats"
        
        # Headers for ESPN API
        self.espn_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Headers for NBA Stats API
        self.nba_headers = {
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
        
    def make_api_request(self, url, headers=None, params=None):
        """Make API request with proper rate limiting and error handling"""
        try:
            time.sleep(self.request_delay)
            
            if headers is None:
                headers = self.espn_headers
                
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning("Rate limited. Waiting 5 seconds...")
                time.sleep(5)
                return self.make_api_request(url, headers, params)
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text[:200]}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {str(e)}")
            return None
    
    def get_wnba_teams_espn(self):
        """Get WNBA teams from ESPN API"""
        logger.info("Fetching WNBA teams from ESPN API...")
        
        url = f"{self.espn_base_url}/teams"
        data = self.make_api_request(url, self.espn_headers)
        
        if not data or 'sports' not in data:
            logger.error("Failed to fetch teams from ESPN API")
            return []
        
        try:
            teams = []
            sport_data = data['sports'][0]
            leagues = sport_data.get('leagues', [])
            
            if leagues:
                league_teams = leagues[0].get('teams', [])
                for team_data in league_teams:
                    team = team_data.get('team', {})
                    teams.append({
                        'espn_id': team.get('id'),
                        'name': team.get('displayName', ''),
                        'abbreviation': team.get('abbreviation', ''),
                        'location': team.get('location', '')
                    })
            
            logger.info(f"Found {len(teams)} WNBA teams from ESPN")
            return teams
            
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error parsing ESPN teams data: {str(e)}")
            return []
    
    def get_team_roster_espn(self, team_id):
        """Get team roster from ESPN API"""
        logger.info(f"Fetching roster for team {team_id} from ESPN...")
        
        url = f"{self.espn_base_url}/teams/{team_id}"
        data = self.make_api_request(url, self.espn_headers)
        
        if not data or 'team' not in data:
            return []
        
        try:
            players = []
            team_data = data['team']
            athletes = team_data.get('athletes', [])
            
            for athlete in athletes:
                players.append({
                    'espn_id': athlete.get('id'),
                    'name': athlete.get('displayName', ''),
                    'position': athlete.get('position', {}).get('name', ''),
                    'jersey': athlete.get('jersey', '')
                })
            
            logger.info(f"Found {len(players)} players for team {team_id}")
            return players
            
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error parsing ESPN roster for team {team_id}: {str(e)}")
            return []
    
    def get_games_espn(self, start_date="2025-05-16", end_date="2025-09-11"):
        """Get all WNBA games from ESPN API for the 2025 season"""
        logger.info(f"Fetching WNBA games from {start_date} to {end_date}...")
        
        all_games = []
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
        
        while current_date <= end_datetime:
            date_str = current_date.strftime("%Y%m%d")
            url = f"{self.espn_base_url}/scoreboard"
            params = {'dates': date_str}
            
            logger.info(f"Fetching games for {current_date.strftime('%Y-%m-%d')}")
            data = self.make_api_request(url, self.espn_headers, params)
            
            if data and 'events' in data:
                for event in data['events']:
                    try:
                        # Extract game data
                        competition = event['competitions'][0]
                        competitors = competition['competitors']
                        
                        home_team = next(c for c in competitors if c['homeAway'] == 'home')
                        away_team = next(c for c in competitors if c['homeAway'] == 'away')
                        
                        game_info = {
                            'game_id': event['id'],
                            'date': event['date'][:10],  # Extract just the date part
                            'home_team_id': home_team['team']['id'],
                            'home_team_name': home_team['team']['displayName'],
                            'home_team_abbr': home_team['team']['abbreviation'],
                            'away_team_id': away_team['team']['id'], 
                            'away_team_name': away_team['team']['displayName'],
                            'away_team_abbr': away_team['team']['abbreviation'],
                            'status': event['status']['type']['description']
                        }
                        
                        all_games.append(game_info)
                        
                    except (KeyError, IndexError) as e:
                        logger.warning(f"Error parsing game data: {str(e)}")
                        continue
            
            # Move to next day
            current_date += timedelta(days=1)
            
            # Add delay to be respectful to ESPN
            time.sleep(0.1)
        
        logger.info(f"Found {len(all_games)} total games")
        return all_games
    
    def get_player_stats_from_game(self, game_id):
        """Get player statistics from a specific game using correct ESPN structure"""
        logger.info(f"Fetching player stats for game {game_id}")
        
        url = f"{self.espn_base_url}/summary"
        params = {'event': game_id}
        
        data = self.make_api_request(url, self.espn_headers, params)
        
        if not data:
            return []
        
        try:
            all_player_stats = []
            
            # Get game date from header
            game_date = ''
            header = data.get('header', {})
            if 'competitions' in header and header['competitions']:
                game_date = header['competitions'][0].get('date', '')[:10]
            
            # Extract boxscore player data - THIS IS THE CORRECT STRUCTURE
            boxscore = data.get('boxscore', {})
            player_sections = boxscore.get('players', [])  # This contains team player data
            
            for team_section in player_sections:
                # Get team info
                team_info = team_section.get('team', {})
                team_id = team_info.get('id')
                team_name = team_info.get('displayName') 
                team_abbr = team_info.get('abbreviation')
                
                # Get player statistics
                statistics = team_section.get('statistics', [])
                if not statistics:
                    continue
                
                # Get the first (and usually only) stats section
                stat_section = statistics[0]
                stat_names = stat_section.get('names', [])
                athletes = stat_section.get('athletes', [])
                
                # ESP stat names: ['MIN', 'FG', '3PT', 'FT', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TO', 'PF', '+/-', 'PTS']
                
                for athlete_data in athletes:
                    player_info = athlete_data.get('athlete', {})
                    stats_array = athlete_data.get('stats', [])
                    
                    if not stats_array:
                        continue
                    
                    # Create stat dictionary mapping names to values
                    stat_dict = {}
                    for i, stat_value in enumerate(stats_array):
                        if i < len(stat_names):
                            stat_dict[stat_names[i]] = stat_value
                    
                    # Parse shooting stats (format: "made-attempted")
                    def parse_shooting_stat(stat_str):
                        if '-' in str(stat_str):
                            parts = str(stat_str).split('-')
                            return self._safe_int(parts[0]), self._safe_int(parts[1])
                        return 0, 0
                    
                    # Extract shooting data
                    fg_made, fg_attempted = parse_shooting_stat(stat_dict.get('FG', '0-0'))
                    fg3_made, fg3_attempted = parse_shooting_stat(stat_dict.get('3PT', '0-0'))
                    ft_made, ft_attempted = parse_shooting_stat(stat_dict.get('FT', '0-0'))
                    
                    # Calculate percentages
                    fg_pct = (fg_made / fg_attempted) if fg_attempted > 0 else 0.0
                    fg3_pct = (fg3_made / fg3_attempted) if fg3_attempted > 0 else 0.0  
                    ft_pct = (ft_made / ft_attempted) if ft_attempted > 0 else 0.0
                    
                    # Convert minutes (could be "34" or "34:30")
                    minutes_raw = stat_dict.get('MIN', '0')
                    if ':' in str(minutes_raw):
                        min_parts = str(minutes_raw).split(':')
                        minutes_decimal = float(min_parts[0]) + float(min_parts[1]) / 60.0
                    else:
                        minutes_decimal = self._safe_float(minutes_raw)
                    
                    # Build complete player stats matching your format
                    player_stats = {
                        'SEASON_YEAR': 2025,
                        'PLAYER_ID': player_info.get('id', ''),
                        'PLAYER_NAME': player_info.get('displayName', ''),
                        'NICKNAME': '',
                        'TEAM_ID': team_id,
                        'TEAM_ABBREVIATION': team_abbr,
                        'TEAM_NAME': team_name,
                        'GAME_ID': game_id,
                        'GAME_DATE': game_date,
                        'MATCHUP': f"{team_abbr} vs OPP",  # Simplified for now
                        'WL': 'W',  # TODO: Determine from game result
                        'MIN': minutes_decimal,
                        'FGM': fg_made,
                        'FGA': fg_attempted,
                        'FG_PCT': round(fg_pct, 3),
                        'FG3M': fg3_made,
                        'FG3A': fg3_attempted,
                        'FG3_PCT': round(fg3_pct, 3),
                        'FTM': ft_made,
                        'FTA': ft_attempted,
                        'FT_PCT': round(ft_pct, 3),
                        'OREB': self._safe_int(stat_dict.get('OREB', 0)),
                        'DREB': self._safe_int(stat_dict.get('DREB', 0)),
                        'REB': self._safe_int(stat_dict.get('REB', 0)),
                        'AST': self._safe_int(stat_dict.get('AST', 0)),
                        'TOV': self._safe_int(stat_dict.get('TO', 0)),
                        'STL': self._safe_int(stat_dict.get('STL', 0)),
                        'BLK': self._safe_int(stat_dict.get('BLK', 0)),
                        'BLKA': 0,  # Not available in ESPN
                        'PF': self._safe_int(stat_dict.get('PF', 0)),
                        'PFD': 0,  # Not available in ESPN
                        'PTS': self._safe_int(stat_dict.get('PTS', 0)),
                        'PLUS_MINUS': self._safe_int(stat_dict.get('+/-', 0)),
                        'NBA_FANTASY_PTS': 0,  # Will calculate
                        'DD2': 0,  # Will calculate
                        'TD3': 0,  # Will calculate
                        'WNBA_FANTASY_PTS': 0,  # Will calculate
                        
                        # Ranking fields - set to null, filled by pipeline
                        'GP_RANK': None, 'W_RANK': None, 'L_RANK': None, 'W_PCT_RANK': None,
                        'MIN_RANK': None, 'FGM_RANK': None, 'FGA_RANK': None, 'FG_PCT_RANK': None,
                        'FG3M_RANK': None, 'FG3A_RANK': None, 'FG3_PCT_RANK': None, 'FTM_RANK': None,
                        'FTA_RANK': None, 'FT_PCT_RANK': None, 'OREB_RANK': None, 'DREB_RANK': None,
                        'REB_RANK': None, 'AST_RANK': None, 'TOV_RANK': None, 'STL_RANK': None,
                        'BLK_RANK': None, 'BLKA_RANK': None, 'PF_RANK': None, 'PFD_RANK': None,
                        'PTS_RANK': None, 'PLUS_MINUS_RANK': None, 'NBA_FANTASY_PTS_RANK': None,
                        'DD2_RANK': None, 'TD3_RANK': None, 'WNBA_FANTASY_PTS_RANK': None,
                        'AVAILABLE_FLAG': 1,
                        'MIN_SEC': str(minutes_raw)
                    }
                    
                    all_player_stats.append(player_stats)
            
            logger.info(f"Successfully extracted {len(all_player_stats)} player stats for game {game_id}")
            return all_player_stats
            
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error parsing player stats for game {game_id}: {str(e)}")
            return []
    
    def _safe_int(self, value):
        """Safely convert value to int"""
        try:
            return int(float(str(value))) if value else 0
        except:
            return 0
    
    def _safe_float(self, value):
        """Safely convert value to float"""
        try:
            return float(str(value)) if value else 0.0
        except:
            return 0.0
    
    def run_full_ingestion(self):
        """Run complete ingestion process using ESPN API"""
        logger.info("Starting WNBA live game log ingestion via ESPN API...")
        
        # Get all games from the 2025 season
        games = self.get_games_espn()
        if not games:
            logger.error("No games found. Aborting.")
            return False
        
        all_game_logs = []
        completed_games = [g for g in games if g['status'] == 'Final']
        logger.info(f"Found {len(completed_games)} completed games to process")
        
        # Process each completed game
        for i, game in enumerate(completed_games):  # Process all completed games
            logger.info(f"Processing game {i+1}/{len(completed_games[:50])}: {game['away_team_abbr']} @ {game['home_team_abbr']}")
            
            try:
                player_stats = self.get_player_stats_from_game(game['game_id'])
                all_game_logs.extend(player_stats)
                
                # Progress update every 10 games
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i+1} games, collected {len(all_game_logs)} player game logs")
                
            except Exception as e:
                logger.error(f"Error processing game {game['game_id']}: {str(e)}")
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
            
            logger.info(f"Successfully saved {len(df)} game logs to {output_path}")
            logger.info(f"Date range: {df['GAME_DATE'].min()} to {df['GAME_DATE'].max()}")
            logger.info(f"Output format matches wnba_2024_gamelogs.csv with {len(column_order)} columns")
            logger.info(f"Players covered: {df['PLAYER_NAME'].nunique()}")
            
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