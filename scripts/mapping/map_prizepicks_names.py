#!/usr/bin/env python3
"""
Map PrizePicks player names to Basketball Reference canonical names.
"""

import pandas as pd
from rapidfuzz import fuzz, process
import os

def main():
    # Read input files
    props_df = pd.read_csv('data/wnba_prizepicks_props.csv')
    directory_df = pd.read_csv('data/player_directory.csv')
    
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    # Initialize lists for matched and unmatched rows
    matched_rows = []
    unmatched_rows = []
    
    # Create a dictionary for exact matching
    name_to_bbref = {
        row['name']: row['BBRefID'] 
        for _, row in directory_df.iterrows()
    }
    
    # Prepare list of all names for fuzzy matching
    all_names = directory_df['name'].tolist()
    
    # Process each row in props data
    for _, prop_row in props_df.iterrows():
        player_name = prop_row['player_name']
        matched = False
        
        # Try exact match first
        if player_name in name_to_bbref:
            matched_rows.append({
                'player_name': prop_row['player_name'],
                'team_name': prop_row['team_name'],
                'stat_type': prop_row['stat_type'],
                'line': prop_row['line'],
                'timestamp': prop_row['timestamp'],
                'matched_name': player_name,
                'bbref_id': name_to_bbref[player_name]
            })
            matched = True
        else:
            # Try fuzzy match
            best_match = process.extractOne(
                player_name, 
                all_names, 
                scorer=fuzz.ratio
            )
            
            if best_match and best_match[1] >= 90:
                matched_name = best_match[0]
                matched_rows.append({
                    'player_name': prop_row['player_name'],
                    'team_name': prop_row['team_name'],
                    'stat_type': prop_row['stat_type'],
                    'line': prop_row['line'],
                    'timestamp': prop_row['timestamp'],
                    'matched_name': matched_name,
                    'bbref_id': name_to_bbref[matched_name]
                })
                matched = True
        
        # If no match found, add to unmatched
        if not matched:
            unmatched_rows.append(prop_row.to_dict())
    
    # Create output DataFrames
    matched_df = pd.DataFrame(matched_rows)
    unmatched_df = pd.DataFrame(unmatched_rows)
    
    # Save output files
    matched_df.to_csv('data/wnba_props_mapped.csv', index=False)
    unmatched_df.to_csv('output/unmatched_players.csv', index=False)
    
    print(f"Matched: {len(matched_rows)} rows")
    print(f"Unmatched: {len(unmatched_rows)} rows")
    print(f"Total: {len(props_df)} rows")

if __name__ == "__main__":
    main()

# Sample output (first 3 mapped rows):
# player_name,team_name,stat_type,line,timestamp,matched_name,bbref_id
# Marina Mabrey,CONN,Points,14.5,2025-06-16 14:30:00,Marina Mabrey,mabrema01w
# A'ja Wilson,LV,Rebounds,11.5,2025-06-16 14:30:00,A'ja Wilson,wilsoaj01w
# Alyssa Thomas,CONN,Assists,7.5,2025-06-16 14:30:00,Alyssa Thomas,thomaal01w