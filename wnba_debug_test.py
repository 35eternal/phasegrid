import pytest
pytest.skip('Temporarily skipping due to missing dependencies', allow_module_level=True)

#!/usr/bin/env python3
"""
Debug test for WNBA Basketball Reference access.
"""

import requests
from bs4 import BeautifulSoup
import time

def test_basketball_ref_access():
    """Test different approaches to Basketball Reference WNBA data."""
    
    print("🔍 Testing Basketball Reference WNBA Access\n")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Test 1: WNBA main page
    print("TEST 1: WNBA main page")
    try:
        url = "https://www.basketball-reference.com/wnba/"
        response = requests.get(url, headers=headers)
        print(f"✅ Status: {response.status_code}")
        if "WNBA" in response.text:
            print("✅ Contains WNBA content")
        else:
            print("❌ No WNBA content found")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    time.sleep(2)
    
    # Test 2: 2024 WNBA season page
    print("\nTEST 2: 2024 WNBA season page")
    try:
        url = "https://www.basketball-reference.com/wnba/years/2024.html"
        response = requests.get(url, headers=headers)
        print(f"✅ Status: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for team links
        team_links = soup.find_all('a', href=lambda x: x and '/wnba/teams/' in x)
        print(f"✅ Found {len(team_links)} team links")
        
        # Show first few team links
        for i, link in enumerate(team_links[:5]):
            print(f"  {i+1}. {link.get('href')} - {link.text.strip()}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    time.sleep(2)
    
    # Test 3: Try a specific team page
    print("\nTEST 3: Indiana Fever team page")
    try:
        url = "https://www.basketball-reference.com/wnba/teams/IND/2024.html"
        response = requests.get(url, headers=headers)
        print(f"✅ Status: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for Caitlin Clark specifically
        clark_links = soup.find_all('a', string=lambda x: x and 'Clark' in x)
        print(f"✅ Found {len(clark_links)} Clark references")
        
        for link in clark_links:
            print(f"  Clark link: {link.get('href')} - {link.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    time.sleep(2)
    
    # Test 4: Try direct player URL patterns
    print("\nTEST 4: Try different Caitlin Clark URL patterns")
    
    possible_urls = [
        "https://www.basketball-reference.com/wnba/players/c/clarkcai01.html",
        "https://www.basketball-reference.com/wnba/players/c/clarkca01.html", 
        "https://www.basketball-reference.com/wnba/players/c/clarkcai01/gamelog/2024",
        "https://www.basketball-reference.com/players/c/clarkcai01.html",  # NBA page maybe?
    ]
    
    for url in possible_urls:
        try:
            response = requests.get(url, headers=headers)
            print(f"  {url}: Status {response.status_code}")
            if response.status_code == 200:
                print(f"    ✅ SUCCESS! Found working URL")
                break
        except Exception as e:
            print(f"  {url}: Error {e}")
        time.sleep(1)
    
    print("\n📋 RECOMMENDATIONS:")
    print("1. If Test 1-2 work: Basketball Reference has WNBA data")
    print("2. If Test 3 works: We can get team rosters") 
    print("3. If Test 4 finds a working URL: We can get individual player data")
    print("4. If nothing works: We need a different data source")

if __name__ == "__main__":
    test_basketball_ref_access()
