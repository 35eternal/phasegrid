#!/usr/bin/env python3
"""
Complete end-to-end player mapping system
Reads PrizePicks data and maps to Basketball Reference
"""
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from fuzzywuzzy import fuzz
import csv
import os
from datetime import datetime

def load_prizepicks_players():
    """Load player names from the latest PrizePicks data"""
    try:
        df = pd.read_csv("data/wnba_prizepicks_props.csv")
        
        # Get unique player names (excluding Unknown/empty)
        unique_players = df['player_name'].dropna().unique()
        valid_players = [name for name in unique_players if not name.startswith(('Unknown', 'No_Player'))]
        
        print(f"📋 Found {len(valid_players)} unique players from PrizePicks:")
        for player in sorted(valid_players):
            print(f"  - {player}")
        
        return valid_players
        
    except Exception as e:
        print(f"❌ Error loading PrizePicks data: {e}")
        return []

def scrape_basketball_reference_players():
    """Scrape current WNBA player list from Basketball Reference"""
    print(f"\n🏀 Scraping Basketball Reference for WNBA players...")
    
    players = {}
    
    # WNBA team abbreviations
    teams = ['ATL', 'CHI', 'CONN', 'DAL', 'IND', 'LAS', 'MIN', 'NY', 'PHX', 'SEA', 'WAS', 'GS']
    
    for team in teams:
        try:
            url = f"https://www.basketball-reference.com/wnba/teams/{team}/2024.html"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for roster table - try multiple possible IDs/classes
            roster_table = (soup.find('table', {'id': 'roster'}) or 
                          soup.find('table', {'class': 'stats_table'}) or
                          soup.find('table', string=re.compile('Player', re.I)))
            
            if roster_table:
                rows = roster_table.find_all('tr')
                
                for row in rows:
                    # Look for player name link
                    name_cell = row.find('td', {'data-stat': 'player'}) or row.find('th', {'data-stat': 'player'})
                    
                    if name_cell:
                        name_link = name_cell.find('a')
                        if name_link:
                            player_name = name_link.text.strip()
                            
                            # Get position if available
                            pos_cell = row.find('td', {'data-stat': 'pos'})
                            position = pos_cell.text.strip() if pos_cell else ''
                            
                            players[player_name] = {
                                'team': team,
                                'position': position,
                                'url': f"https://www.basketball-reference.com{name_link.get('href', '')}"
                            }
                
                print(f"  ✅ {team}: {len([p for p in players.values() if p['team'] == team])} players")
            else:
                print(f"  ⚠️ {team}: No roster table found")
                
        except Exception as e:
            print(f"  ❌ {team}: Error - {e}")
    
    print(f"\n📊 Total Basketball Reference players: {len(players)}")
    return players

def normalize_name(name):
    """Normalize player name for matching"""
    if not name:
        return ""
    
    # Remove suffixes
    name = re.sub(r'\s+(Jr\.?|Sr\.?|III|II|IV)$', '', name, flags=re.IGNORECASE)
    
    # Remove special characters
    name = re.sub(r"[.'']", '', name)
    
    # Convert to lowercase
    name = ' '.join(name.lower().split())
    
    return name

def find_best_match(prizepicks_name, bbref_players, threshold=80):
    """Find best Basketball Reference match for PrizePicks name"""
    
    normalized_pp = normalize_name(prizepicks_name)
    
    best_match = None
    best_score = 0
    
    for bbref_name in bbref_players.keys():
        normalized_bbref = normalize_name(bbref_name)
        
        # Try different matching approaches
        scores = [
            fuzz.ratio(normalized_pp, normalized_bbref),
            fuzz.partial_ratio(normalized_pp, normalized_bbref),
            fuzz.token_sort_ratio(normalized_pp, normalized_bbref),
            fuzz.token_set_ratio(normalized_pp, normalized_bbref)
        ]
        
        max_score = max(scores)
        
        if max_score > best_score and max_score >= threshold:
            best_score = max_score
            best_match = bbref_name
    
    return best_match, best_score

def run_complete_mapping():
    """Run the complete mapping process"""
    print("🔗 Starting Complete Player Mapping Process\n")
    
    # Step 1: Load PrizePicks players
    prizepicks_players = load_prizepicks_players()
    
    if not prizepicks_players:
        print("❌ No PrizePicks players found. Exiting.")
        return
    
    # Step 2: Scrape Basketball Reference
    bbref_players = scrape_basketball_reference_players()
    
    if not bbref_players:
        print("❌ No Basketball Reference players found. Exiting.")
        return
    
    # Step 3: Perform mapping
    print(f"\n🔍 Mapping {len(prizepicks_players)} PrizePicks players...\n")
    
    mappings = []
    successful_maps = 0
    
    for pp_name in prizepicks_players:
        bbref_match, confidence = find_best_match(pp_name, bbref_players)
        
        if bbref_match:
            mappings.append({
                'prizepicks_name': pp_name,
                'bbref_name': bbref_match,
                'confidence': confidence,
                'team': bbref_players[bbref_match]['team'],
                'position': bbref_players[bbref_match]['position'],
                'bbref_url': bbref_players[bbref_match]['url'],
                'status': 'auto_mapped'
            })
            
            print(f"✅ {pp_name} → {bbref_match} ({confidence}% confidence)")
            successful_maps += 1
            
        else:
            mappings.append({
                'prizepicks_name': pp_name,
                'bbref_name': '',
                'confidence': 0,
                'team': '',
                'position': '',
                'bbref_url': '',
                'status': 'needs_review'
            })
            
            print(f"❌ {pp_name} → No match found")
    
    # Step 4: Save mappings
    mapping_file = "data/player_final_mapping.csv"
    os.makedirs("data", exist_ok=True)
    
    with open(mapping_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'prizepicks_name', 'bbref_name', 'confidence', 'team', 
            'position', 'bbref_url', 'status'
        ])
        writer.writeheader()
        writer.writerows(mappings)
    
    # Step 5: Results summary
    print(f"\n📊 MAPPING RESULTS:")
    print(f"  Total players: {len(prizepicks_players)}")
    print(f"  Successfully mapped: {successful_maps}")
    print(f"  Need manual review: {len(prizepicks_players) - successful_maps}")
    print(f"  Success rate: {(successful_maps/len(prizepicks_players)*100):.1f}%")
    
    print(f"\n💾 Mappings saved to: {mapping_file}")
    
    # Show unmapped players
    unmapped = [m for m in mappings if m['status'] == 'needs_review']
    if unmapped:
        print(f"\n⚠️ Players needing manual review:")
        for player in unmapped:
            print(f"  - {player['prizepicks_name']}")
    
    return mappings

if __name__ == "__main__":
    mappings = run_complete_mapping()
    
    print(f"\n✅ Player mapping complete!")
    print(f"🔗 Next step: Run your analysis with mapped player names")