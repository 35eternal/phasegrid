#!/usr/bin/env python3
"""
Scrape WNBA rosters from Basketball Reference 2025 season.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

def get_team_rosters():
    """Get all WNBA team rosters for 2025 season."""
    base_url = "https://www.basketball-reference.com"
    players = []
    
    # WNBA teams and their abbreviations
    teams = {
        'ATL': 'Atlanta Dream',
        'CHI': 'Chicago Sky', 
        'CON': 'Connecticut Sun',
        'DAL': 'Dallas Wings',
        'IND': 'Indiana Fever',
        'LA': 'Los Angeles Sparks',
        'LAS': 'Las Vegas Aces',
        'MIN': 'Minnesota Lynx',
        'NY': 'New York Liberty',
        'PHO': 'Phoenix Mercury',
        'SEA': 'Seattle Storm',
        'WAS': 'Washington Mystics'
    }
    
    for team_abbr, team_name in teams.items():
        print(f"Scraping {team_name} roster...")
        url = f"{base_url}/wnba/teams/{team_abbr}/2025.html"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the roster table
            roster_table = soup.find('table', {'id': 'roster'})
            if not roster_table:
                print(f"  No roster table found for {team_name}")
                continue
            
            # Get all player rows
            tbody = roster_table.find('tbody')
            if tbody:
                for row in tbody.find_all('tr'):
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        # First cell should contain player link
                        player_cell = cells[0]
                        player_link = player_cell.find('a')
                        
                        if player_link:
                            player_name = player_link.text.strip()
                            player_url = base_url + player_link['href']
                            bbref_id = player_link['href'].split('/')[-1].replace('.html', '')
                            
                            players.append({
                                'name': player_name,
                                'BBRefID': bbref_id,
                                'url': player_url,
                                'team': team_abbr,
                                'team_name': team_name
                            })
            
            # Be respectful to the server
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  Error scraping {team_name}: {e}")
            continue
    
    return players

def create_player_directory():
    """Create and save the player directory from team rosters."""
    print("Starting Basketball Reference roster scrape...")
    players = get_team_rosters()
    
    if players:
        # Convert to DataFrame
        df = pd.DataFrame(players)
        
        # Remove duplicates (players who switched teams)
        df = df.drop_duplicates(subset=['BBRefID'], keep='last')
        
        # Sort by name
        df = df.sort_values('name')
        
        # Save to CSV
        df.to_csv('data/player_directory.csv', index=False)
        print(f"\nSuccessfully scraped {len(df)} WNBA players!")
        print(f"Saved to data/player_directory.csv")
        
        # Show sample
        print("\nSample of scraped players:")
        print(df[['name', 'BBRefID', 'team']].head(10))
        
        # Show some names that should match your props
        print("\nChecking for Marina Mabrey...")
        marina = df[df['name'].str.contains('Marina', case=False, na=False)]
        if not marina.empty:
            print(marina[['name', 'BBRefID', 'team']])
        else:
            print("Marina Mabrey not found - might need manual addition")
    else:
        print("No players found!")

if __name__ == "__main__":
    create_player_directory()