#!/usr/bin/env python3
"""
Fetch Basketball Reference game logs for all mapped players
"""
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import os
from datetime import datetime

def load_mapped_players():
    """Load the successfully mapped players"""
    try:
        df = pd.read_csv("data/player_final_mapping.csv")
        mapped_players = df[df['bbref_name'] != ''].copy()
        
        print(f"📋 Found {len(mapped_players)} mapped players:")
        for _, player in mapped_players.iterrows():
            print(f"  - {player['prizepicks_name']} → {player['bbref_name']} ({player['team']})")
        
        return mapped_players
        
    except Exception as e:
        print(f"❌ Error loading mappings: {e}")
        return pd.DataFrame()

def fetch_player_gamelog(bbref_url, player_name):
    """Fetch game log for a specific player"""
    
    print(f"📊 Fetching game log: {player_name}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        # Modify URL to get 2024 game log
        if '/players/' in bbref_url:
            # Convert player page URL to game log URL
            # Example: /players/l/loydje01w.html → /players/l/loydje01w/gamelog/2024
            base_url = bbref_url.replace('.html', '/gamelog/2024')
        else:
            print(f"  ⚠️ Invalid URL format: {bbref_url}")
            return None
        
        response = requests.get(base_url, headers=headers)
        
        if response.status_code != 200:
            print(f"  ❌ HTTP {response.status_code} for {player_name}")
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find game log table
        gamelog_table = soup.find('table', {'id': 'gamelog'})
        
        if not gamelog_table:
            print(f"  ⚠️ No game log table found for {player_name}")
            return None
        
        # Parse table into DataFrame
        rows = []
        header_row = gamelog_table.find('thead').find('tr')
        headers = [th.get('data-stat', th.text.strip()) for th in header_row.find_all('th')]
        
        tbody = gamelog_table.find('tbody')
        for row in tbody.find_all('tr'):
            if 'thead' in row.get('class', []):  # Skip header rows in body
                continue
                
            row_data = {}
            cells = row.find_all(['td', 'th'])
            
            for i, cell in enumerate(cells):
                if i < len(headers):
                    stat = cell.get('data-stat', headers[i])
                    value = cell.text.strip()
                    row_data[stat] = value
            
            if row_data:  # Only add non-empty rows
                row_data['player_name'] = player_name
                rows.append(row_data)
        
        if rows:
            df = pd.DataFrame(rows)
            print(f"  ✅ Found {len(df)} games for {player_name}")
            return df
        else:
            print(f"  ⚠️ No game data found for {player_name}")
            return None
            
    except Exception as e:
        print(f"  ❌ Error fetching {player_name}: {e}")
        return None

def fetch_all_mapped_gamelogs():
    """Fetch game logs for all mapped players"""
    
    print("🏀 Fetching game logs for mapped players...\n")
    
    # Load mapped players
    mapped_players = load_mapped_players()
    
    if mapped_players.empty:
        print("❌ No mapped players found")
        return
    
    all_gamelogs = []
    
    for _, player in mapped_players.iterrows():
        bbref_url = player['bbref_url']
        bbref_name = player['bbref_name']
        prizepicks_name = player['prizepicks_name']
        
        # Fetch game log
        gamelog_df = fetch_player_gamelog(bbref_url, bbref_name)
        
        if gamelog_df is not None:
            # Add player mapping info
            gamelog_df['bbref_name'] = bbref_name
            gamelog_df['prizepicks_name'] = prizepicks_name
            gamelog_df['team'] = player['team']
            
            all_gamelogs.append(gamelog_df)
        
        # Rate limiting
        time.sleep(1)
        print()
    
    if all_gamelogs:
        # Combine all game logs
        combined_df = pd.concat(all_gamelogs, ignore_index=True)
        
        # Clean up data types
        numeric_cols = ['pts', 'ast', 'trb', 'stl', 'blk', 'tov', 'fg3', 'fg3a', 'fg', 'fga', 'ft', 'fta']
        
        for col in numeric_cols:
            if col in combined_df.columns:
                combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce')
        
        # Save to CSV
        output_file = "data/mapped_player_gamelogs.csv"
        combined_df.to_csv(output_file, index=False)
        
        print(f"📊 GAME LOG SUMMARY:")
        print(f"  Total players: {len(mapped_players)}")
        print(f"  Players with data: {len(all_gamelogs)}")
        print(f"  Total games: {len(combined_df)}")
        print(f"  Date range: {combined_df['date_game'].min()} to {combined_df['date_game'].max()}")
        
        print(f"\n💾 Game logs saved to: {output_file}")
        
        # Show sample data
        print(f"\n🔍 Sample game log data:")
        sample_cols = ['player_name', 'date_game', 'pts', 'ast', 'trb']
        available_cols = [col for col in sample_cols if col in combined_df.columns]
        print(combined_df[available_cols].head(10).to_string(index=False))
        
        return combined_df
        
    else:
        print("❌ No game logs retrieved")
        return None

def create_analysis_ready_dataset():
    """Merge props with game logs for analysis"""
    
    print(f"\n🔗 Creating analysis-ready dataset...\n")
    
    try:
        # Load props and game logs
        props_df = pd.read_csv("data/wnba_prizepicks_props.csv")
        gamelogs_df = pd.read_csv("data/mapped_player_gamelogs.csv")
        
        print(f"📋 Props data: {len(props_df)} rows")
        print(f"📊 Game logs: {len(gamelogs_df)} rows")
        
        # Merge on player name
        merged_df = props_df.merge(
            gamelogs_df,
            left_on='player_name',
            right_on='prizepicks_name',
            how='left'
        )
        
        print(f"🔗 Merged dataset: {len(merged_df)} rows")
        
        # Save analysis-ready dataset
        output_file = "data/analysis_ready_dataset.csv"
        merged_df.to_csv(output_file, index=False)
        
        print(f"💾 Analysis-ready dataset saved to: {output_file}")
        
        # Show merge success rate
        props_with_gamelogs = merged_df['pts'].notna().sum()
        merge_rate = (props_with_gamelogs / len(props_df)) * 100
        print(f"📈 Merge success rate: {merge_rate:.1f}%")
        
        return merged_df
        
    except Exception as e:
        print(f"❌ Error creating analysis dataset: {e}")
        return None

if __name__ == "__main__":
    print("🏀 Fetching Game Logs for Mapped Players\n")
    
    # Step 1: Fetch all game logs
    gamelogs = fetch_all_mapped_gamelogs()
    
    if gamelogs is not None:
        # Step 2: Create analysis-ready dataset
        analysis_df = create_analysis_ready_dataset()
        
        if analysis_df is not None:
            print(f"\n✅ Ready for analysis!")
            print(f"🔗 Run: python -c \"from core.analyzer import analyze_props; analyze_props()\"")
        else:
            print(f"\n❌ Failed to create analysis dataset")
    else:
        print(f"\n❌ Failed to fetch game logs")