#!/usr/bin/env python3
"""
Enhanced player mapping with correct team codes and manual overrides
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
    """Scrape WNBA players with corrected team codes"""
    print(f"\n🏀 Scraping Basketball Reference (Enhanced)...")
    
    players = {}
    
    # Corrected team codes - try multiple variations and years
    team_configs = [
        # Format: (team_code, year)
        ('ATL', 2024), ('CHI', 2024), ('CON', 2024), ('DAL', 2024),
        ('IND', 2024), ('LAS', 2024), ('MIN', 2024), ('NYL', 2024),
        ('PHX', 2024), ('SEA', 2024), ('WAS', 2024), ('LV', 2024),
        # Try 2025 if available
        ('ATL', 2025), ('CHI', 2025), ('CON', 2025), ('DAL', 2025),
        ('IND', 2025), ('LAS', 2025), ('MIN', 2025), ('NYL', 2025),
        ('PHX', 2025), ('SEA', 2025), ('WAS', 2025), ('LV', 2025)
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    successful_teams = set()
    
    for team_code, year in team_configs:
        # Skip if we already got this team successfully
        if team_code in successful_teams:
            continue
            
        try:
            url = f"https://www.basketball-reference.com/wnba/teams/{team_code}/{year}.html"
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                continue
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple ways to find the roster table
            roster_table = None
            for table_id in ['roster', 'per_game', 'stats']:
                roster_table = soup.find('table', {'id': table_id})
                if roster_table:
                    break
            
            if not roster_table:
                roster_table = soup.find('table', {'class': 'stats_table'})
            
            if roster_table:
                rows = roster_table.find_all('tr')
                team_players = 0
                
                for row in rows:
                    # Look for player name
                    name_cell = (row.find('td', {'data-stat': 'player'}) or 
                               row.find('th', {'data-stat': 'player'}) or
                               row.find('td', {'data-stat': 'name'}))
                    
                    if name_cell:
                        name_link = name_cell.find('a')
                        if name_link:
                            player_name = name_link.text.strip()
                            
                            # Get position if available
                            pos_cell = row.find('td', {'data-stat': 'pos'})
                            position = pos_cell.text.strip() if pos_cell else ''
                            
                            # Only add if not already present (avoid duplicates)
                            if player_name not in players:
                                players[player_name] = {
                                    'team': team_code,
                                    'position': position,
                                    'year': year,
                                    'url': f"https://www.basketball-reference.com{name_link.get('href', '')}"
                                }
                                team_players += 1
                
                if team_players > 0:
                    successful_teams.add(team_code)
                    print(f"  ✅ {team_code} ({year}): {team_players} players")
                else:
                    print(f"  ⚠️ {team_code} ({year}): Table found but no players")
            else:
                print(f"  ❌ {team_code} ({year}): No roster table")
                
        except Exception as e:
            print(f"  💥 {team_code} ({year}): {e}")
    
    print(f"\n📊 Total Basketball Reference players: {len(players)}")
    return players

def get_manual_overrides():
    """Manual name mappings for known mismatches"""
    return {
        'Chelsea Gray': 'Chelsea Gray',  # Exact match should work
        'Jackie Young': 'Jackie Young',  # Exact match should work  
        'Alyssa Thomas': 'Alyssa Thomas',  # Exact match should work
        'Jewell Loyd': 'Jewell Loyd',
        'Satou Sabally': 'Satou Sabally'
    }

def normalize_name(name):
    """Enhanced name normalization"""
    if not name:
        return ""
    
    # Remove suffixes
    name = re.sub(r'\s+(Jr\.?|Sr\.?|III|II|IV)$', '', name, flags=re.IGNORECASE)
    
    # Remove special characters but preserve spaces
    name = re.sub(r"[.'']", '', name)
    
    # Handle common variations
    name = name.replace(' Jr', '').replace(' Sr', '')
    
    # Convert to lowercase and normalize whitespace
    name = ' '.join(name.lower().split())
    
    return name

def find_best_match(prizepicks_name, bbref_players, threshold=75):
    """Enhanced matching with multiple algorithms"""
    
    normalized_pp = normalize_name(prizepicks_name)
    
    best_match = None
    best_score = 0
    
    for bbref_name in bbref_players.keys():
        normalized_bbref = normalize_name(bbref_name)
        
        # Multiple matching strategies
        scores = [
            fuzz.ratio(normalized_pp, normalized_bbref),
            fuzz.partial_ratio(normalized_pp, normalized_bbref),
            fuzz.token_sort_ratio(normalized_pp, normalized_bbref),
            fuzz.token_set_ratio(normalized_pp, normalized_bbref)
        ]
        
        # Also try matching individual names
        pp_parts = normalized_pp.split()
        bbref_parts = normalized_bbref.split()
        
        if len(pp_parts) >= 2 and len(bbref_parts) >= 2:
            # Try first + last name matching
            pp_first_last = f"{pp_parts[0]} {pp_parts[-1]}"
            bbref_first_last = f"{bbref_parts[0]} {bbref_parts[-1]}"
            scores.append(fuzz.ratio(pp_first_last, bbref_first_last))
        
        max_score = max(scores)
        
        if max_score > best_score and max_score >= threshold:
            best_score = max_score
            best_match = bbref_name
    
    return best_match, best_score

def run_enhanced_mapping():
    """Run enhanced mapping with fixes"""
    print("🔗 Enhanced Player Mapping Process\n")
    
    # Step 1: Load PrizePicks players
    prizepicks_players = load_prizepicks_players()
    if not prizepicks_players:
        return
    
    # Step 2: Get manual overrides
    manual_overrides = get_manual_overrides()
    
    # Step 3: Scrape Basketball Reference with corrections
    bbref_players = scrape_basketball_reference_players()
    if not bbref_players:
        return
    
    # Step 4: Enhanced mapping
    print(f"\n🔍 Enhanced mapping process...\n")
    
    mappings = []
    successful_maps = 0
    
    for pp_name in prizepicks_players:
        # Check manual overrides first
        if pp_name in manual_overrides:
            manual_bbref = manual_overrides[pp_name]
            if manual_bbref in bbref_players:
                mappings.append({
                    'prizepicks_name': pp_name,
                    'bbref_name': manual_bbref,
                    'confidence': 100,
                    'team': bbref_players[manual_bbref]['team'],
                    'position': bbref_players[manual_bbref]['position'],
                    'bbref_url': bbref_players[manual_bbref]['url'],
                    'status': 'manual_override'
                })
                print(f"✅ {pp_name} → {manual_bbref} (manual override)")
                successful_maps += 1
                continue
        
        # Try automatic matching
        bbref_match, confidence = find_best_match(pp_name, bbref_players, threshold=75)
        
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
    
    # Step 5: Save results
    mapping_file = "data/player_final_mapping.csv"
    os.makedirs("data", exist_ok=True)
    
    with open(mapping_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'prizepicks_name', 'bbref_name', 'confidence', 'team', 
            'position', 'bbref_url', 'status'
        ])
        writer.writeheader()
        writer.writerows(mappings)
    
    # Step 6: Results
    print(f"\n📊 ENHANCED MAPPING RESULTS:")
    print(f"  Total players: {len(prizepicks_players)}")
    print(f"  Successfully mapped: {successful_maps}")
    print(f"  Need manual review: {len(prizepicks_players) - successful_maps}")
    print(f"  Success rate: {(successful_maps/len(prizepicks_players)*100):.1f}%")
    
    print(f"\n💾 Enhanced mappings saved to: {mapping_file}")
    
    # Show available players for manual matching
    unmapped = [m for m in mappings if m['status'] == 'needs_review']
    if unmapped:
        print(f"\n⚠️ Players needing manual review:")
        for player in unmapped:
            print(f"  - {player['prizepicks_name']}")
        
        # Show similar Basketball Reference players
        print(f"\n🔍 Available Basketball Reference players (for manual review):")
        for name in sorted(bbref_players.keys())[:20]:  # Show first 20
            print(f"  - {name}")
    
    return mappings

if __name__ == "__main__":
    mappings = run_enhanced_mapping()
    
    print(f"\n✅ Enhanced mapping complete!")
    print(f"📋 Check data/player_final_mapping.csv for results")