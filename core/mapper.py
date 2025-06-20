#!/usr/bin/env python3
"""
auto_player_mapper.py - Automated WNBA Player Mapping System
Maps PrizePicks player names to Basketball Reference IDs using fuzzy matching
"""

import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
from datetime import datetime
import logging
import sys
from pathlib import Path
import os

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/player_mapping.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class WNBAPlayerMapper:
    def __init__(self, mapping_csv_path='player_final_mapping.csv', 
                 props_json_path='wnba_prizepicks_props.json',
                 confidence_threshold=85):
        """
        Initialize the mapper with file paths and matching threshold
        
        Args:
            mapping_csv_path: Path to existing player mapping CSV
            props_json_path: Path to PrizePicks props JSON
            confidence_threshold: Minimum fuzzy match score (0-100) to auto-accept
        """
        self.mapping_csv_path = mapping_csv_path
        self.props_json_path = props_json_path
        self.confidence_threshold = confidence_threshold
        self.bbref_players = {}
        
    def load_existing_mappings(self):
        """Load current player mappings from CSV"""
        try:
            self.existing_mappings = pd.read_csv(self.mapping_csv_path)
            # Rename columns to match our expected structure
            if 'name' in self.existing_mappings.columns:
                self.existing_mappings = self.existing_mappings.rename(columns={
                    'name': 'prizepicks_name',
                    'BBRefID': 'bbref_id'
                })
            # Add missing columns if they don't exist
            for col in ['bbref_name', 'confidence_score', 'mapping_date', 'auto_mapped']:
                if col not in self.existing_mappings.columns:
                    self.existing_mappings[col] = None
            
            logging.info(f"Loaded {len(self.existing_mappings)} existing mappings")
            return self.existing_mappings
        except FileNotFoundError:
            logging.warning(f"No existing mapping file found at {self.mapping_csv_path}")
            # Create empty DataFrame with expected structure
            self.existing_mappings = pd.DataFrame(columns=[
                'prizepicks_name', 'bbref_id', 'bbref_name', 
                'confidence_score', 'mapping_date', 'auto_mapped'
            ])
            return self.existing_mappings
    
    def scrape_bbref_players(self, year=2025):
        """Scrape all WNBA players from Basketball Reference"""
        logging.info(f"Scraping WNBA players from Basketball Reference for {year}")
        
        url = f"https://www.basketball-reference.com/wnba/years/{year}_per_game.html"
        
        try:
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', {'id': 'per_game_stats'})
            
            if not table:
                logging.error("Could not find player stats table")
                return {}
            
            # Extract player data
            for row in table.find_all('tr')[1:]:  # Skip header
                player_cell = row.find('td', {'data-stat': 'player'})
                if player_cell and player_cell.find('a'):
                    link = player_cell.find('a')
                    player_name = link.text.strip()
                    player_id = link['href'].split('/')[-1].replace('.html', '')
                    
                    # Store multiple name formats for better matching
                    self.bbref_players[player_id] = {
                        'full_name': player_name,
                        'last_first': self._format_last_first(player_name),
                        'normalized': self._normalize_name(player_name)
                    }
            
            logging.info(f"Found {len(self.bbref_players)} players on Basketball Reference")
            return self.bbref_players
            
        except Exception as e:
            logging.error(f"Error scraping Basketball Reference: {e}")
            return {}
    
    def _format_last_first(self, name):
        """Convert 'First Last' to 'Last, First' format"""
        parts = name.split()
        if len(parts) >= 2:
            return f"{parts[-1]}, {' '.join(parts[:-1])}"
        return name
    
    def _normalize_name(self, name):
        """Normalize name for matching (lowercase, remove punctuation)"""
        import re
        normalized = re.sub(r'[^\w\s]', '', name.lower())
        return ' '.join(normalized.split())
    
    def load_prizepicks_players(self):
        """Extract unique player names from PrizePicks props"""
        try:
            with open(self.props_json_path, 'r') as f:
                props_data = json.load(f)
            
            players = set()
            
            # Players are in the 'included' array with type 'new_player'
            if 'included' in props_data:
                for item in props_data['included']:
                    if item.get('type') == 'new_player':
                        player_name = item['attributes']['name']
                        # Skip combo players (they contain '+')
                        if '+' not in player_name:
                            players.add(player_name)
                        else:
                            # Handle combo players by splitting them
                            for p in player_name.split('+'):
                                players.add(p.strip())
            
            logging.info(f"Found {len(players)} unique players in PrizePicks data")
            return list(players)
            
        except Exception as e:
            logging.error(f"Error loading PrizePicks data: {e}")
            return []
    
    def find_best_match(self, prizepicks_name):
        """Find best matching BBRef player for a PrizePicks name"""
        best_match = None
        best_score = 0
        best_id = None
        
        normalized_pp = self._normalize_name(prizepicks_name)
        
        for bbref_id, bbref_data in self.bbref_players.items():
            # Try different matching strategies
            scores = [
                fuzz.ratio(prizepicks_name, bbref_data['full_name']),
                fuzz.ratio(prizepicks_name, bbref_data['last_first']),
                fuzz.ratio(normalized_pp, bbref_data['normalized']),
                fuzz.token_sort_ratio(prizepicks_name, bbref_data['full_name']),
                fuzz.token_set_ratio(prizepicks_name, bbref_data['full_name'])
            ]
            
            max_score = max(scores)
            
            if max_score > best_score:
                best_score = max_score
                best_match = bbref_data['full_name']
                best_id = bbref_id
        
        return best_id, best_match, best_score
    
    def map_new_players(self):
        """Main function to map unmapped PrizePicks players"""
        # Load existing data
        self.load_existing_mappings()
        
        # Get BBRef players
        if not self.bbref_players:
            self.scrape_bbref_players()
        
        # Get PrizePicks players
        pp_players = self.load_prizepicks_players()
        
        # Find unmapped players
        mapped_names = set(self.existing_mappings['prizepicks_name'].values)
        unmapped_players = [p for p in pp_players if p not in mapped_names]
        
        logging.info(f"Found {len(unmapped_players)} unmapped players")
        
        if not unmapped_players:
            logging.info("All players already mapped!")
            return self.existing_mappings
        
        # Map each unmapped player
        new_mappings = []
        for pp_name in unmapped_players:
            bbref_id, bbref_name, score = self.find_best_match(pp_name)
            
            if score >= self.confidence_threshold:
                logging.info(f"AUTO-MAPPED: {pp_name} -> {bbref_name} (score: {score})")
                new_mappings.append({
                    'prizepicks_name': pp_name,
                    'bbref_id': bbref_id,
                    'bbref_name': bbref_name,
                    'confidence_score': score,
                    'mapping_date': datetime.now().strftime('%Y-%m-%d'),
                    'auto_mapped': True
                })
            else:
                logging.warning(f"LOW CONFIDENCE: {pp_name} -> {bbref_name} (score: {score})")
                # Still add but flag for manual review
                new_mappings.append({
                    'prizepicks_name': pp_name,
                    'bbref_id': bbref_id if score > 60 else None,
                    'bbref_name': bbref_name if score > 60 else None,
                    'confidence_score': score,
                    'mapping_date': datetime.now().strftime('%Y-%m-%d'),
                    'auto_mapped': False
                })
        
        # Combine with existing mappings
        if new_mappings:
            new_df = pd.DataFrame(new_mappings)
            updated_mappings = pd.concat([self.existing_mappings, new_df], ignore_index=True)
            
            # Save updated mappings with original column names
            save_df = updated_mappings.copy()
            # Convert back to original column names for compatibility
            save_df = save_df.rename(columns={
                'prizepicks_name': 'name',
                'bbref_id': 'BBRefID'
            })
            # Only save the essential columns to match original format
            save_df = save_df[['name', 'BBRefID']]
            save_df.to_csv(self.mapping_csv_path, index=False)
            logging.info(f"Saved {len(new_mappings)} new mappings to {self.mapping_csv_path}")
            
            # Save full details including low-confidence mappings for review
            review_df = new_df[new_df['confidence_score'] < self.confidence_threshold]
            if len(review_df) > 0:
                # Save in data folder
                review_df.to_csv('data/mappings_for_review.csv', index=False)
                logging.info(f"Saved {len(review_df)} low-confidence mappings for manual review")
            
            return updated_mappings
        
        return self.existing_mappings
    
    def validate_mappings(self):
        """Validate existing mappings by checking if BBRef IDs still exist"""
        logging.info("Validating existing mappings...")
        
        if not self.bbref_players:
            self.scrape_bbref_players()
        
        if not hasattr(self, 'existing_mappings') or self.existing_mappings.empty:
            self.load_existing_mappings()
        
        invalid_mappings = []
        for idx, row in self.existing_mappings.iterrows():
            if pd.notna(row['bbref_id']) and row['bbref_id'] not in self.bbref_players:
                invalid_mappings.append(row['prizepicks_name'])
        
        if invalid_mappings:
            logging.warning(f"Found {len(invalid_mappings)} invalid mappings: {invalid_mappings}")
        else:
            logging.info("All mappings validated successfully")
        
        return invalid_mappings


def main():
    """Run the automated mapping process"""
    # Initialize mapper - adjust paths to your data folder
    mapper = WNBAPlayerMapper(
        mapping_csv_path='data/player_final_mapping.csv',
        props_json_path='data/wnba_prizepicks_props.json',
        confidence_threshold=85  # Adjust based on testing
    )
    
    # Run mapping process
    updated_mappings = mapper.map_new_players()
    
    # Validate existing mappings
    mapper.validate_mappings()
    
    # Summary statistics
    total_mapped = len(updated_mappings[updated_mappings['bbref_id'].notna()])
    auto_mapped = len(updated_mappings[(updated_mappings['auto_mapped'] == True) & 
                                      (updated_mappings['bbref_id'].notna())])
    needs_review = len(updated_mappings[(updated_mappings['bbref_id'].isna()) | 
                                       (updated_mappings['auto_mapped'] == False)])
    
    print(f"\n=== Mapping Summary ===")
    print(f"Total Players Found: {len(updated_mappings)}")
    print(f"Successfully Mapped: {total_mapped}")
    print(f"Auto-Mapped: {auto_mapped}")
    print(f"Needs Review: {needs_review}")
    
    # Show recent mappings
    if len(updated_mappings) > 0:
        print("\n=== Recent Mappings ===")
        recent = updated_mappings[updated_mappings['mapping_date'].notna()].sort_values(
            'mapping_date', ascending=False).head(10)
        if len(recent) > 0:
            display_cols = ['prizepicks_name', 'bbref_name', 'confidence_score', 'auto_mapped']
            # Only show columns that exist
            display_cols = [col for col in display_cols if col in recent.columns]
            print(recent[display_cols])


if __name__ == "__main__":
    main()