#!/usr/bin/env python3
"""
Debug Basketball Reference game log URLs
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd

def test_gamelog_url_formats():
    """Test different URL formats for Basketball Reference game logs"""
    
    print("🔍 Testing Basketball Reference Game Log URL Formats\n")
    
    # Test with Jewell Loyd as example
    test_player = {
        'name': 'Jewell Loyd',
        'url': 'https://www.basketball-reference.com/wnba/players/l/loydje01w.html'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Extract player ID from URL
    player_id = test_player['url'].split('/')[-1].replace('.html', '')
    player_path = '/'.join(test_player['url'].split('/')[:-1])
    
    print(f"🧪 Testing player: {test_player['name']}")
    print(f"Player ID: {player_id}")
    print(f"Player path: {player_path}")
    print()
    
    # Different URL formats to try
    url_formats = [
        f"{player_path}/{player_id}/gamelog/2024",
        f"{player_path}/{player_id}/gamelog-advanced/2024", 
        f"https://www.basketball-reference.com/wnba/players/{player_id[0]}/{player_id}/gamelog/2024",
        f"https://www.basketball-reference.com/wnba/players/{player_id[0]}/{player_id}/gamelog-advanced/2024",
        f"https://www.basketball-reference.com/wnba/players/{player_id[0]}/{player_id}.html",
        test_player['url'],  # Original player page
    ]
    
    for i, url in enumerate(url_formats, 1):
        print(f"🔍 Format {i}: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for different types of tables
                tables = soup.find_all('table')
                table_ids = [t.get('id') for t in tables if t.get('id')]
                
                print(f"  ✅ Page loaded successfully")
                print(f"  Tables found: {len(tables)}")
                print(f"  Table IDs: {table_ids}")
                
                # Check for game log specific tables
                gamelog_tables = [
                    soup.find('table', {'id': 'gamelog'}),
                    soup.find('table', {'id': 'pgl_basic'}),
                    soup.find('table', {'id': 'gamelog_basic'}),
                    soup.find('table', {'id': 'stats'}),
                ]
                
                gamelog_found = any(table is not None for table in gamelog_tables)
                
                if gamelog_found:
                    print(f"  🎯 GAME LOG TABLE FOUND!")
                    
                    # Try to parse a few rows
                    for table in gamelog_tables:
                        if table is not None:
                            rows = table.find_all('tr')
                            print(f"    Table rows: {len(rows)}")
                            
                            # Show sample row
                            if len(rows) > 1:
                                sample_row = rows[1]  # Skip header
                                cells = sample_row.find_all(['td', 'th'])
                                sample_data = [cell.text.strip() for cell in cells[:5]]
                                print(f"    Sample data: {sample_data}")
                            break
                    
                    return url  # Return working URL
                    
                else:
                    print(f"  ⚠️ No game log tables found")
                    
            elif response.status_code == 404:
                print(f"  ❌ Page not found")
            elif response.status_code == 500:
                print(f"  ❌ Server error")
            else:
                print(f"  ⚠️ Unexpected status")
                
        except Exception as e:
            print(f"  💥 Error: {e}")
        
        print()
    
    print("❌ No working game log URL format found")
    return None

def check_2025_season():
    """Check if 2025 season data is available"""
    
    print("📅 Checking 2025 WNBA season data availability...\n")
    
    # Check if Basketball Reference has 2025 season data yet
    test_urls = [
        "https://www.basketball-reference.com/wnba/years/2025.html",
        "https://www.basketball-reference.com/wnba/years/2024.html",
        "https://www.basketball-reference.com/wnba/"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for url in test_urls:
        try:
            response = requests.get(url, headers=headers)
            year = url.split('/')[-1].replace('.html', '')
            
            print(f"🔍 {year}: HTTP {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for current season info
                page_text = soup.get_text().lower()
                
                if '2025' in page_text:
                    print(f"  ✅ 2025 season data found")
                elif '2024' in page_text:
                    print(f"  📊 2024 season data available")
                
        except Exception as e:
            print(f"  💥 Error: {e}")

def suggest_alternative_data_source():
    """Suggest alternative ways to get player performance data"""
    
    print(f"\n💡 Alternative Data Solutions:\n")
    
    print(f"1. 🔄 Use existing data:")
    print(f"   - Check if you have historical WNBA data files")
    print(f"   - Look for data/wnba_2024_gamelogs.csv")
    print(f"   - Use any existing player performance data")
    
    print(f"\n2. 📊 Simplified analysis:")
    print(f"   - Calculate edges based on season averages")
    print(f"   - Use league-wide statistical baselines")
    print(f"   - Focus on current props only")
    
    print(f"\n3. 🌐 Alternative APIs:")
    print(f"   - WNBA official stats API")
    print(f"   - ESPN or other sports data sources")
    print(f"   - Free sports data APIs")

if __name__ == "__main__":
    print("🏀 Basketball Reference Game Log URL Debug\n")
    
    working_url = test_gamelog_url_formats()
    check_2025_season()
    suggest_alternative_data_source()
    
    if working_url:
        print(f"\n✅ Working URL format found: {working_url}")
    else:
        print(f"\n❌ Need to find alternative data source")