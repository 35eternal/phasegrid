#!/usr/bin/env python3
"""
Extract unique players from WNBA gamelogs and create player directory.
"""

import pandas as pd
import re

def generate_bbref_id(player_name):
    """
    Generate a BBRef ID from player name using standard format.
    Format: first 5 letters of last name + first 2 of first name + 01w
    """
    if not player_name or pd.isna(player_name):
        return None
        
    # Clean the name
    name = player_name.strip()
    parts = name.split()
    
    if len(parts) < 2:
        return None
    
    # Handle names with suffixes (Jr., III, etc.)
    if parts[-1] in ['Jr.', 'Jr', 'III', 'II', 'Sr.', 'Sr']:
        last_name = parts[-2]
        first_name = parts[0]
    else:
        last_name = parts[-1]
        first_name = parts[0]
    
    # Clean and format
    last_name = re.sub(r'[^a-zA-Z]', '', last_name.lower())
    first_name = re.sub(r'[^a-zA-Z]', '', first_name.lower())
    
    # BBRef format
    last_part = last_name[:5].ljust(5, last_name[-1] if last_name else 'x')
    first_part = first_name[:2].ljust(2, first_name[-1] if first_name else 'x')
    
    return f"{last_part}{first_part}01w"

def create_player_directory_from_gamelogs():
    """Extract players from gamelogs and create directory."""
    print("Reading gamelogs...")
    
    # Read both 2024 and 2025 gamelogs if available
    all_players = []
    
    # Try 2025 gamelogs
    try:
        df_2025 = pd.read_csv('data/wnba_2025_gamelogs.csv')
        players_2025 = df_2025[['PLAYER_NAME', 'TEAM_ABBREVIATION']].drop_duplicates()
        players_2025['season'] = 2025
        all_players.append(players_2025)
        print(f"Found {len(players_2025)} unique players in 2025 gamelogs")
    except:
        print("No 2025 gamelogs found")
    
    # Try 2024 gamelogs  
    try:
        df_2024 = pd.read_csv('data/wnba_2024_gamelogs.csv')
        players_2024 = df_2024[['PLAYER_NAME', 'TEAM_ABBREVIATION']].drop_duplicates()
        players_2024['season'] = 2024
        all_players.append(players_2024)
        print(f"Found {len(players_2024)} unique players in 2024 gamelogs")
    except:
        print("No 2024 gamelogs found")
    
    # Try combined gamelogs
    try:
        df_combined = pd.read_csv('data/wnba_combined_gamelogs.csv')
        players_combined = df_combined[['PLAYER_NAME', 'TEAM_ABBREVIATION']].drop_duplicates()
        players_combined['season'] = 2025  # Assume current
        all_players.append(players_combined)
        print(f"Found {len(players_combined)} unique players in combined gamelogs")
    except:
        print("No combined gamelogs found")
    
    if not all_players:
        print("No gamelogs found!")
        return
    
    # Combine all players
    players_df = pd.concat(all_players, ignore_index=True)
    
    # Get most recent team for each player
    players_df = players_df.sort_values('season', ascending=False)
    players_df = players_df.drop_duplicates(subset=['PLAYER_NAME'], keep='first')
    
    # Generate BBRef IDs
    players_df['BBRefID'] = players_df['PLAYER_NAME'].apply(generate_bbref_id)
    
    # Create final directory
    directory_df = pd.DataFrame({
        'name': players_df['PLAYER_NAME'],
        'BBRefID': players_df['BBRefID'],
        'team': players_df['TEAM_ABBREVIATION'],
        'last_season': players_df['season']
    })
    
    # Remove any rows with missing names or IDs
    directory_df = directory_df.dropna(subset=['name', 'BBRefID'])
    
    # Sort by name
    directory_df = directory_df.sort_values('name')
    
    # Save
    directory_df.to_csv('data/player_directory.csv', index=False)
    print(f"\nSuccessfully created directory with {len(directory_df)} players!")
    print(f"Saved to data/player_directory.csv")
    
    # Show sample
    print("\nSample players:")
    print(directory_df.head(10))
    
    # Check for Marina Mabrey
    print("\nChecking for Marina Mabrey...")
    marina = directory_df[directory_df['name'].str.contains('Marina', case=False, na=False)]
    if not marina.empty:
        print(marina)
    else:
        print("Marina Mabrey not found in gamelogs")

if __name__ == "__main__":
    create_player_directory_from_gamelogs()