#!/usr/bin/env python3
"""
Scrape all active WNBA players from Basketball Reference to create player directory.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

def get_all_wnba_players():
    """Scrape all WNBA players from Basketball Reference."""
    base_url = "https://www.basketball-reference.com"
    players = []
    
    # Get players by first letter of last name
    for letter in 'abcdefghijklmnopqrstuvwxyz':
        print(f"Scraping players with last names starting with '{letter.upper()}'...")
        url = f"{base_url}/wnba/players/{letter}/"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the players table
            players_table = soup.find('table', {'id': 'players'})
            if not players_table:
                continue
                
            # Get all player rows
            for row in players_table.find('tbody').find_all('tr'):
                # Skip non-player rows
                if row.get('class') and 'thead' in row.get('class'):
                    continue
                    
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 8:  # Make sure we have all needed columns
                    player_link = cells[0].find('a')
                    if player_link:
                        player_name = player_link.text.strip()
                        player_url = base_url + player_link['href']
                        bbref_id = player_link['href'].split('/')[-1].replace('.html', '')
                        
                        # Get years active
                        years = cells[1].text.strip()
                        if years:  # Only include players who have played
                            year_parts = years.split('-')
                            if len(year_parts) == 2:
                                last_year = int(year_parts[1])
                                # Include if played in 2024 or 2025
                                if last_year >= 2024:
                                    players.append({
                                        'name': player_name,
                                        'BBRefID': bbref_id,
                                        'url': player_url,
                                        'years_active': years,
                                        'last_year': last_year
                                    })
            
            # Be respectful to the server
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error scraping letter {letter}: {e}")
            continue
    
    return players

def create_player_directory():
    """Create and save the player directory."""
    print("Starting Basketball Reference scrape...")
    players = get_all_wnba_players()
    
    if players:
        # Convert to DataFrame
        df = pd.DataFrame(players)
        
        # Sort by name
        df = df.sort_values('name')
        
        # Save to CSV
        df.to_csv('data/player_directory.csv', index=False)
        print(f"\nSuccessfully scraped {len(players)} active WNBA players!")
        print(f"Saved to data/player_directory.csv")
        
        # Show sample
        print("\nSample of scraped players:")
        print(df[['name', 'BBRefID', 'last_year']].head(10))
    else:
        print("No players found!")

if __name__ == "__main__":
    create_player_directory()