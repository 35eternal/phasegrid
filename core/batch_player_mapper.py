#!/usr/bin/env python3
"""
WNBA Player Mapping Scaler - Integrated with existing project structure
Scales player mapping from 5 players to full WNBA rosters with intelligent rate limiting.
"""

import pandas as pd
import requests
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from fuzzywuzzy import fuzz
import random
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config import *  # Import project configuration

@dataclass
class MappingConfig:
    """Configuration for the mapping process"""
    requests_per_minute: int = 30
    requests_per_hour: int = 1000
    retry_attempts: int = 3
    backoff_factor: float = 2.0
    fuzzy_threshold: int = 85
    batch_size: int = 10
    enable_proxies: bool = False
    proxy_list: List[str] = None
    data_dir: Path = Path("data")
    output_dir: Path = Path("output")

class RateLimiter:
    """Intelligent rate limiter with exponential backoff"""
    
    def __init__(self, config: MappingConfig):
        self.config = config
        self.request_times = []
        self.hourly_count = 0
        self.last_hour_reset = datetime.now().hour
        
    def wait_if_needed(self):
        """Wait if we're approaching rate limits"""
        now = datetime.now()
        current_hour = now.hour
        
        # Reset hourly counter
        if current_hour != self.last_hour_reset:
            self.hourly_count = 0
            self.last_hour_reset = current_hour
            
        # Remove requests older than 1 minute
        minute_ago = now.timestamp() - 60
        self.request_times = [t for t in self.request_times if t > minute_ago]
        
        # Check minute limit
        if len(self.request_times) >= self.config.requests_per_minute:
            sleep_time = 60 - (now.timestamp() - self.request_times[0])
            if sleep_time > 0:
                logging.info(f"Rate limit approaching, sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
                
        # Check hourly limit
        if self.hourly_count >= self.config.requests_per_hour:
            sleep_time = 3600 - ((now.minute * 60) + now.second)
            logging.info(f"Hourly limit reached, sleeping {sleep_time}s")
            time.sleep(sleep_time)
            self.hourly_count = 0
            
    def record_request(self):
        """Record that we made a request"""
        self.request_times.append(datetime.now().timestamp())
        self.hourly_count += 1

class PlayerMappingScaler:
    """Main class for scaling player mapping operations"""
    
    def __init__(self, config: MappingConfig = None):
        self.config = config or MappingConfig()
        self.rate_limiter = RateLimiter(self.config)
        self.session = requests.Session()
        self.setup_logging()
        
        # Ensure data directory exists
        self.config.data_dir.mkdir(exist_ok=True)
        self.config.output_dir.mkdir(exist_ok=True)
        
        # Load existing data
        self.existing_mapping = self.load_existing_mapping()
        self.mapped_players = set(self.existing_mapping.keys()) if self.existing_mapping else set()
        
        # Stats tracking
        self.stats = {
            'total_attempted': 0,
            'successful_mappings': 0,
            'failed_mappings': 0,
            'skipped_existing': 0,
            'api_calls_made': 0,
            'fuzzy_matches': 0
        }
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = self.config.data_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'player_mapping.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_existing_mapping(self) -> Dict[str, str]:
        """Load existing player mappings to avoid duplicates"""
        try:
            mapping_file = self.config.data_dir / 'player_final_mapping.csv'
            if mapping_file.exists():
                df = pd.read_csv(mapping_file)
                self.logger.info(f"Loaded {len(df)} existing player mappings")
                return dict(zip(df['PrizePicks_Name'], df['BBRef_ID']))
        except Exception as e:
            self.logger.warning(f"Could not load existing mapping: {e}")
        return {}
    
    def get_all_wnba_players_from_props(self) -> List[str]:
        """Extract all unique player names from current props"""
        props_files = [
            'wnba_prizepicks_props.csv',
            'prizepicks_wnba_props.csv',
            'props_prizepicks.csv'
        ]
        
        for filename in props_files:
            try:
                props_file = self.config.data_dir / filename
                if props_file.exists():
                    props_df = pd.read_csv(props_file)
                    
                    # Try different column names for player names
                    player_columns = ['player_name', 'Player', 'name', 'Player_Name']
                    player_col = None
                    
                    for col in player_columns:
                        if col in props_df.columns:
                            player_col = col
                            break
                    
                    if player_col:
                        unique_players = props_df[player_col].dropna().unique().tolist()
                        self.logger.info(f"Found {len(unique_players)} unique players in {filename}")
                        return unique_players
                        
            except Exception as e:
                self.logger.warning(f"Could not load {filename}: {e}")
                continue
                
        self.logger.error("Could not find any props data files")
        return []
    
    def fuzzy_match_player(self, prizepicks_name: str, bbref_players: List[Dict]) -> Optional[str]:
        """Use fuzzy matching to find best player match"""
        best_match = None
        best_score = 0
        best_name = ""
        
        for player in bbref_players:
            bbref_name = player.get('name', '')
            score = fuzz.ratio(prizepicks_name.lower(), bbref_name.lower())
            
            if score > best_score and score >= self.config.fuzzy_threshold:
                best_score = score
                best_match = player.get('id')
                best_name = bbref_name
                
        if best_match:
            self.stats['fuzzy_matches'] += 1
            self.logger.info(f"Fuzzy match: '{prizepicks_name}' -> '{best_name}' (score: {best_score})")
            
        return best_match
    
    def search_basketball_reference(self, player_name: str) -> Optional[str]:
        """Search Basketball Reference for player ID with retry logic"""
        for attempt in range(self.config.retry_attempts):
            try:
                self.rate_limiter.wait_if_needed()
                
                # Mock Basketball Reference API search
                # TODO: Replace with actual BBRef scraping/API integration
                search_url = f"https://www.basketball-reference.com/search/search.fcgi"
                params = {'search': player_name, 'pid': 'pls', 'idx': 'wnba'}
                
                response = self.session.get(search_url, params=params, timeout=10)
                self.rate_limiter.record_request()
                self.stats['api_calls_made'] += 1
                
                if response.status_code == 200:
                    # Parse response to extract player ID
                    player_id = self.parse_search_results(response.text, player_name)
                    return player_id
                    
                elif response.status_code == 429:  # Rate limited
                    wait_time = self.config.backoff_factor ** attempt
                    self.logger.warning(f"Rate limited, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue
                    
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {player_name}: {e}")
                if attempt < self.config.retry_attempts - 1:
                    time.sleep(self.config.backoff_factor ** attempt)
                    
        return None
    
    def parse_search_results(self, html_content: str, player_name: str) -> Optional[str]:
        """Parse Basketball Reference search results"""
        # TODO: Implement actual HTML parsing logic here
        # For now, return a mock ID format that can be used for testing
        mock_id = player_name.lower().replace(' ', '').replace("'", '')[:8] + '01'
        
        # Add some randomness to simulate real behavior
        if random.random() > 0.8:  # 20% failure rate for testing
            return None
            
        return mock_id
    
    def map_single_player(self, player_name: str) -> Tuple[bool, str, str]:
        """Map a single player name to Basketball Reference ID"""
        # Skip if already mapped
        if player_name in self.mapped_players:
            self.stats['skipped_existing'] += 1
            return True, self.existing_mapping[player_name], "Already mapped"
            
        self.logger.info(f"Mapping player: {player_name}")
        self.stats['total_attempted'] += 1
        
        # Search Basketball Reference
        bbref_id = self.search_basketball_reference(player_name)
        
        if bbref_id:
            self.stats['successful_mappings'] += 1
            self.mapped_players.add(player_name)
            return True, bbref_id, "Successfully mapped"
        else:
            self.stats['failed_mappings'] += 1
            return False, "", "No match found"
    
    def process_batch(self, player_names: List[str]) -> List[Dict]:
        """Process a batch of players"""
        results = []
        
        for player_name in player_names:
            success, bbref_id, status = self.map_single_player(player_name)
            
            result = {
                'PrizePicks_Name': player_name,
                'BBRef_ID': bbref_id if success else '',
                'Status': status,
                'Timestamp': datetime.now().isoformat(),
                'Success': success
            }
            results.append(result)
            
            # Small delay between players in batch
            time.sleep(random.uniform(0.5, 1.5))
            
        return results
    
    def save_results(self, all_results: List[Dict]):
        """Save mapping results to CSV files"""
        # Combine with existing mappings
        all_successful = [r for r in all_results if r['Success']]
        
        if all_successful:
            # Load existing mappings
            existing_df = None
            mapping_file = self.config.data_dir / 'player_final_mapping.csv'
            
            if mapping_file.exists():
                existing_df = pd.read_csv(mapping_file)
            
            # Create new mappings dataframe
            new_df = pd.DataFrame(all_successful)[['PrizePicks_Name', 'BBRef_ID']]
            
            # Combine and save
            if existing_df is not None:
                combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['PrizePicks_Name'])
            else:
                combined_df = new_df
                
            combined_df.to_csv(mapping_file, index=False)
            self.logger.info(f"Saved {len(combined_df)} total player mappings")
        
        # Failed mappings for manual review
        failed = [r for r in all_results if not r['Success']]
        if failed:
            failed_df = pd.DataFrame(failed)
            failed_df.to_csv(self.config.data_dir / 'mapping_errors.csv', index=False)
            self.logger.info(f"Saved {len(failed)} failed mappings for review")
        
        # All results for audit trail
        if all_results:
            all_df = pd.DataFrame(all_results)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audit_file = self.config.output_dir / f'mapping_audit_{timestamp}.csv'
            all_df.to_csv(audit_file, index=False)
    
    def save_metrics(self):
        """Save mapping metrics and statistics"""
        metrics = {
            'run_timestamp': datetime.now().isoformat(),
            'configuration': {
                'requests_per_minute': self.config.requests_per_minute,
                'requests_per_hour': self.config.requests_per_hour,
                'retry_attempts': self.config.retry_attempts,
                'fuzzy_threshold': self.config.fuzzy_threshold,
                'batch_size': self.config.batch_size
            },
            'statistics': self.stats,
            'success_rate': self.stats['successful_mappings'] / max(self.stats['total_attempted'], 1),
            'total_players_mapped': len(self.mapped_players)
        }
        
        metrics_file = self.config.output_dir / 'mapping_metrics.json'
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        self.logger.info(f"Mapping complete. Success rate: {metrics['success_rate']:.1%}")
        self.logger.info(f"Total players now mapped: {metrics['total_players_mapped']}")
    
    def run_full_mapping(self) -> Dict:
        """Run the complete mapping process"""
        self.logger.info("Starting full WNBA player mapping process...")
        
        # Get all players from current props
        all_players = self.get_all_wnba_players_from_props()
        if not all_players:
            self.logger.error("No players found in props data")
            return self.stats
        
        # Filter out already mapped players
        unmapped_players = [p for p in all_players if p not in self.mapped_players]
        self.logger.info(f"Found {len(unmapped_players)} unmapped players out of {len(all_players)} total")
        
        if not unmapped_players:
            self.logger.info("All players already mapped!")
            return self.stats
        
        # Process in batches
        all_results = []
        total_batches = (len(unmapped_players) + self.config.batch_size - 1) // self.config.batch_size
        
        for i in range(0, len(unmapped_players), self.config.batch_size):
            batch_num = (i // self.config.batch_size) + 1
            batch = unmapped_players[i:i + self.config.batch_size]
            
            self.logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} players)")
            batch_results = self.process_batch(batch)
            all_results.extend(batch_results)
            
            # Progress update
            progress = (batch_num / total_batches) * 100
            self.logger.info(f"Progress: {progress:.1f}% complete")
            
            # Longer delay between batches
            if batch_num < total_batches:
                time.sleep(random.uniform(2, 5))
        
        # Save all results
        self.save_results(all_results)
        self.save_metrics()
        
        return self.stats

def main():
    """Main execution function"""
    print("WNBA Player Mapping Scaler")
    print("=" * 50)
    
    # Configuration for production use
    config = MappingConfig(
        requests_per_minute=20,  # Conservative rate limiting
        requests_per_hour=800,
        retry_attempts=3,
        fuzzy_threshold=85,
        batch_size=5,
        enable_proxies=False,  # Set to True if you have proxy list
        data_dir=Path("data"),
        output_dir=Path("output")
    )
    
    # Initialize and run mapper
    mapper = PlayerMappingScaler(config)
    final_stats = mapper.run_full_mapping()
    
    print("\n" + "="*50)
    print("MAPPING COMPLETE - FINAL STATISTICS")
    print("="*50)
    for key, value in final_stats.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    print("="*50)
    
    return final_stats

if __name__ == "__main__":
    main()