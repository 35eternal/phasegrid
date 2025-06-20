#!/usr/bin/env python3
"""
Test script to identify the correct PrizePicks player API endpoint
"""
import requests
import json
import pandas as pd

# Use your existing headers/cookies
HEADERS = {
    "Accept": "application/json",
    "Origin": "https://app.prizepicks.com",
    "Referer": "https://app.prizepicks.com/",
    "User-Agent": "Mozilla/5.0"
}

COOKIES = {
    "_prizepicks_session": "YOUR_SESSION_COOKIE_HERE",  # Replace with actual session
}

def test_player_endpoints():
    """Test different possible player API endpoints"""
    
    # First, get a sample player ID from your existing data
    try:
        df = pd.read_csv("data/wnba_prizepicks_props.csv")
        sample_player_id = df['player_id'].dropna().iloc[0]
        print(f"🧪 Testing with player ID: {sample_player_id}")
    except:
        print("❌ Could not load existing props data")
        return
    
    # Test different potential endpoints
    endpoints_to_test = [
        f"https://api.prizepicks.com/players/{sample_player_id}",
        f"https://api.prizepicks.com/players?ids={sample_player_id}",
        f"https://api.prizepicks.com/players?id={sample_player_id}",
        "https://api.prizepicks.com/players",
        f"https://api.prizepicks.com/new_players/{sample_player_id}",
        f"https://api.prizepicks.com/new_players?ids={sample_player_id}",
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n🔍 Testing: {endpoint}")
        
        try:
            response = requests.get(endpoint, headers=HEADERS, cookies=COOKIES)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ SUCCESS! Response preview:")
                print(f"  {json.dumps(data, indent=2)[:500]}...")
                
                # Look for player name in the response
                if isinstance(data, dict):
                    if 'data' in data:
                        for item in data['data'][:3]:  # Check first 3 items
                            if 'attributes' in item:
                                attrs = item['attributes']
                                name = attrs.get('name') or attrs.get('display_name') or attrs.get('full_name')
                                if name:
                                    print(f"  🎯 Found player name: {name}")
                
                break  # Stop on first success
                
            elif response.status_code == 404:
                print(f"  ❌ Not found")
            elif response.status_code == 403:
                print(f"  🔒 Forbidden - may need authentication")
            else:
                print(f"  ⚠️ Error: {response.status_code}")
                
        except Exception as e:
            print(f"  💥 Exception: {e}")

def analyze_projection_structure():
    """Analyze the structure of existing projections to find player references"""
    
    print(f"\n📋 Analyzing existing projection structure...")
    
    try:
        # Load your existing JSON data
        with open("data/wnba_prizepicks_props.json", 'r') as f:
            props = json.load(f)
            
        if props:
            sample_projection = props[0]
            print(f"🔍 Sample projection structure:")
            print(json.dumps(sample_projection, indent=2))
            
            # Look for player references
            print(f"\n🔍 Looking for player references...")
            if 'relationships' in sample_projection:
                relationships = sample_projection['relationships']
                print(f"Relationships found: {list(relationships.keys())}")
                
                # Check for player-related relationships
                for key in relationships:
                    if 'player' in key.lower():
                        print(f"Player relationship: {key} = {relationships[key]}")
                        
    except Exception as e:
        print(f"❌ Error analyzing projections: {e}")

if __name__ == "__main__":
    print("🧪 PrizePicks Player API Detective\n")
    
    analyze_projection_structure()
    test_player_endpoints()
    
    print(f"\n💡 Next steps:")
    print(f"1. Update your session cookie in COOKIES")
    print(f"2. Run this script to find the working player endpoint")
    print(f"3. Update core/scraper.py with the correct endpoint")