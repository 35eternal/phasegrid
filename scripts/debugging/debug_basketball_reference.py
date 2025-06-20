#!/usr/bin/env python3
"""
Debug Basketball Reference scraping and find correct team codes
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd

def test_team_urls():
    """Test different team URL variations to find correct codes"""
    
    print("🔍 Testing Basketball Reference team URLs...\n")
    
    # Current team codes that failed
    failed_teams = ['CONN', 'NY', 'PHX', 'GS']
    
    # Alternative team codes to try
    team_variations = {
        'CONN': ['CON', 'CONN', 'CONNCONN'],
        'NY': ['NY', 'NYL', 'NYLB', 'NYLI'],
        'PHX': ['PHX', 'PHOENIX'],
        'GS': ['GS', 'GSW', 'GOLD']
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    working_codes = {}
    
    for original_team in failed_teams:
        print(f"🔍 Testing variations for {original_team}:")
        
        found_working = False
        
        for variation in team_variations.get(original_team, [original_team]):
            for year in [2024, 2025]:
                url = f"https://www.basketball-reference.com/wnba/teams/{variation}/{year}.html"
                
                try:
                    response = requests.get(url, headers=headers)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for roster table
                        roster_table = (soup.find('table', {'id': 'roster'}) or 
                                      soup.find('table', {'class': 'stats_table'}))
                        
                        if roster_table:
                            rows = roster_table.find_all('tr')
                            player_count = len([r for r in rows if r.find('td', {'data-stat': 'player'})])
                            
                            print(f"  ✅ {variation}/{year}: {player_count} players found")
                            working_codes[original_team] = {'code': variation, 'year': year}
                            found_working = True
                            break
                        else:
                            print(f"  ⚠️ {variation}/{year}: Page found but no roster table")
                    else:
                        print(f"  ❌ {variation}/{year}: HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"  💥 {variation}/{year}: {e}")
                    
            if found_working:
                break
        
        if not found_working:
            print(f"  ❌ No working URL found for {original_team}")
        
        print()
    
    return working_codes

def check_player_variations():
    """Check what the unmapped players might be called on Basketball Reference"""
    
    print("🔍 Checking unmapped player name variations...\n")
    
    unmapped_players = ['Chelsea Gray', 'Jackie Young', 'Alyssa Thomas']
    
    # Load the players we actually found
    try:
        df = pd.read_csv("data/player_final_mapping.csv")
        mapped_players = df[df['bbref_name'] != '']['bbref_name'].tolist()
        
        print(f"📋 Successfully mapped players:")
        for player in mapped_players:
            print(f"  ✅ {player}")
        
    except Exception as e:
        print(f"❌ Error reading mapping file: {e}")
        return
    
    print(f"\n🔍 Searching for unmapped players in Basketball Reference...")
    
    # Search Basketball Reference for these players
    for player in unmapped_players:
        print(f"\n🔍 Searching for: {player}")
        
        try:
            # Use Basketball Reference search
            search_url = "https://www.basketball-reference.com/search/search.fcgi"
            params = {
                'search': player,
                'pid': 'fz'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(search_url, params=params, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for search results
                search_results = soup.find_all('div', class_='search-item')
                
                if search_results:
                    print(f"  🎯 Search results found:")
                    for i, result in enumerate(search_results[:3]):  # Show top 3
                        name_link = result.find('a')
                        if name_link:
                            name = name_link.text.strip()
                            url = name_link.get('href', '')
                            print(f"    {i+1}. {name} ({url})")
                else:
                    # Try looking in the page content for partial matches
                    page_text = soup.get_text().lower()
                    player_lower = player.lower()
                    
                    if player_lower in page_text:
                        print(f"  ⚠️ Player name found in page but no direct results")
                    else:
                        print(f"  ❌ No search results found")
            else:
                print(f"  ❌ Search failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  💥 Search error: {e}")

def suggest_manual_mappings():
    """Suggest potential manual mappings based on common name variations"""
    
    print("\n💡 Manual mapping suggestions:")
    
    suggestions = {
        'Chelsea Gray': [
            'Chelsea Gray',
            'Chelsea T. Gray', 
            'C. Gray',
            'Gray, Chelsea'
        ],
        'Jackie Young': [
            'Jackie Young',
            'Jacqueline Young',
            'J. Young',
            'Young, Jackie'
        ],
        'Alyssa Thomas': [
            'Alyssa Thomas',
            'A. Thomas',
            'Thomas, Alyssa'
        ]
    }
    
    for player, variations in suggestions.items():
        print(f"\n🔍 {player} might be listed as:")
        for variation in variations:
            print(f"  - {variation}")

if __name__ == "__main__":
    print("🏀 Basketball Reference Debug Tool\n")
    
    # Test team URLs
    working_codes = test_team_urls()
    
    if working_codes:
        print("✅ Working team codes found:")
        for team, info in working_codes.items():
            print(f"  {team} → {info['code']}/{info['year']}")
    
    # Check player variations  
    check_player_variations()
    
    # Suggest manual mappings
    suggest_manual_mappings()
    
    print(f"\n🔧 Next steps:")
    print(f"1. Update team codes in the mapping script")
    print(f"2. Add manual mappings for the 3 unmapped players")
    print(f"3. Re-run the mapping with corrections")