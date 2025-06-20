#!/usr/bin/env python3
"""
Manual lookup for Chelsea Gray and Jackie Young
"""
import requests
from bs4 import BeautifulSoup

def check_las_vegas_roster():
    """Check Las Vegas Aces roster specifically for Chelsea Gray and Jackie Young"""
    
    print("🔍 Checking Las Vegas Aces roster for missing players...\n")
    
    url = "https://www.basketball-reference.com/wnba/teams/LAS/2024.html"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find roster table
        roster_table = soup.find('table', {'id': 'roster'})
        
        if roster_table:
            print("📋 Las Vegas Aces 2024 Roster:")
            
            rows = roster_table.find_all('tr')
            las_players = []
            
            for row in rows:
                name_cell = row.find('td', {'data-stat': 'player'})
                if name_cell and name_cell.find('a'):
                    player_name = name_cell.find('a').text.strip()
                    las_players.append(player_name)
                    print(f"  - {player_name}")
            
            # Check for our target players
            print(f"\n🎯 Looking for target players:")
            
            targets = ['Chelsea Gray', 'Jackie Young']
            found_matches = {}
            
            for target in targets:
                print(f"\n🔍 Searching for: {target}")
                
                # Exact match
                if target in las_players:
                    print(f"  ✅ Exact match found: {target}")
                    found_matches[target] = target
                else:
                    # Fuzzy search
                    target_lower = target.lower()
                    potential_matches = []
                    
                    for player in las_players:
                        player_lower = player.lower()
                        
                        # Check if names are similar
                        target_parts = target_lower.split()
                        player_parts = player_lower.split()
                        
                        # Check if first or last name matches
                        for target_part in target_parts:
                            for player_part in player_parts:
                                if (len(target_part) > 3 and target_part in player_part) or \
                                   (len(player_part) > 3 and player_part in target_part):
                                    potential_matches.append(player)
                                    break
                    
                    if potential_matches:
                        print(f"  🤔 Potential matches:")
                        for match in set(potential_matches):
                            print(f"    - {match}")
                    else:
                        print(f"  ❌ No potential matches found")
            
            return found_matches, las_players
            
        else:
            print("❌ No roster table found")
            return {}, []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return {}, []

def search_other_teams():
    """Search other teams for the missing players"""
    
    print(f"\n🔍 Searching other teams for Chelsea Gray and Jackie Young...\n")
    
    # Teams where they might be
    teams_to_check = ['LV', 'LAS', 'ATL', 'CHI', 'CON', 'DAL', 'IND', 'MIN', 'NYL', 'SEA', 'WAS']
    
    targets = ['Chelsea Gray', 'Jackie Young']
    found_players = {}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for team in teams_to_check:
        try:
            url = f"https://www.basketball-reference.com/wnba/teams/{team}/2024.html"
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                continue
                
            soup = BeautifulSoup(response.content, 'html.parser')
            roster_table = soup.find('table', {'id': 'roster'})
            
            if roster_table:
                rows = roster_table.find_all('tr')
                team_players = []
                
                for row in rows:
                    name_cell = row.find('td', {'data-stat': 'player'})
                    if name_cell and name_cell.find('a'):
                        player_name = name_cell.find('a').text.strip()
                        team_players.append(player_name)
                
                # Check for our targets
                for target in targets:
                    if target in team_players:
                        found_players[target] = {
                            'bbref_name': target,
                            'team': team
                        }
                        print(f"  ✅ Found {target} on {team}")
                
        except Exception as e:
            continue
    
    return found_players

def generate_manual_fix():
    """Generate the manual fix for the mapping file"""
    
    print(f"\n🔧 Generating manual fix...\n")
    
    # Check LAS roster
    las_matches, las_players = check_las_vegas_roster()
    
    # Search other teams  
    other_matches = search_other_teams()
    
    # Combine findings
    all_matches = {**las_matches, **other_matches}
    
    if all_matches:
        print(f"\n✅ Found matches:")
        for target, match_info in all_matches.items():
            if isinstance(match_info, str):
                print(f"  {target} → {match_info}")
            else:
                print(f"  {target} → {match_info['bbref_name']} ({match_info['team']})")
    
    # Generate CSV fix
    print(f"\n📝 Manual CSV fix for data/player_final_mapping.csv:")
    print(f"Replace the needs_review rows with:")
    
    # Provide manual entries based on what we know
    if 'Chelsea Gray' not in all_matches:
        print(f"Chelsea Gray,Chelsea Gray,100,LAS,G,,manual_fix")
    
    if 'Jackie Young' not in all_matches:
        print(f"Jackie Young,Jackie Young,100,LAS,G,,manual_fix")

if __name__ == "__main__":
    print("🔍 Manual Player Lookup Tool\n")
    generate_manual_fix()