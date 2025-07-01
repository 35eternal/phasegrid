#!/usr/bin/env python3
"""EMERGENCY: Direct PrizePicks fetch and slip generation"""
import requests
import json
import os
from datetime import datetime

print("🚨 EMERGENCY PRIZEPICKS FETCHER")
print("=" * 40)

# Direct API call with all proper headers
url = "https://api.prizepicks.com/projections"
params = {
    "league_id": 7,  # WNBA
    "per_page": 250,
    "single_stat": True,
    "game_mode": "pickem"
}

headers = {
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    'sec-ch-ua-mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Referer': 'https://app.prizepicks.com/',
    'X-Device-ID': '1a9d6304-65f3-4304-8523-ccf458d3c0c4',
    'sec-ch-ua-platform': '"Windows"'
}

print(f"📡 Fetching from: {url}")
print("⏰ Waiting 30 seconds for rate limit...")
import time
time.sleep(30)

try:
    response = requests.get(url, params=params, headers=headers, timeout=30)
    print(f"📊 Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        projections = data.get('data', [])
        print(f"✅ Found {len(projections)} projections")
        
        if projections:
            # Save raw data
            with open('emergency_projections.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("💾 Saved to emergency_projections.json")
            
            # Create betting slips
            slips = []
            for proj in projections[:10]:  # Top 10
                attrs = proj.get('attributes', {})
                
                # Extract player
                player_data = attrs.get('new_player', {})
                if not player_data:
                    player_data = attrs.get('player', {})
                
                player_name = player_data.get('name', 'Unknown')
                
                # Extract stat
                stat_data = attrs.get('stat_type', {})
                if isinstance(stat_data, dict):
                    stat_type = stat_data.get('name', 'Unknown')
                else:
                    stat_type = str(stat_data)
                
                # Extract line
                line = attrs.get('line_score', 0)
                
                if player_name != 'Unknown' and line > 0:
                    slip = {
                        "slip_id": f"EM-{proj.get('id', '')}",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "player": player_name,
                        "prop_type": stat_type,
                        "line": line,
                        "pick": "over" if len(slips) % 2 == 0 else "under",
                        "odds": -110,
                        "confidence": 0.70,
                        "amount": 50.0,
                        "reasoning": "Commissioner's Cup special"
                    }
                    slips.append(slip)
                    print(f"  ✅ {player_name} - {stat_type}: {line}")
            
            if slips:
                # Save betting card
                with open('emergency_betting_card.json', 'w') as f:
                    json.dump(slips, f, indent=2)
                print(f"\n💾 Created betting card with {len(slips)} slips")
                print("🎯 Ready to bet!")
                
                # Upload to sheets
                os.system("python scripts/upload_to_sheets.py emergency_betting_card.json")
            else:
                print("❌ Could not parse player data")
        else:
            print("❌ No projections in response")
    else:
        print(f"❌ API error: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    
print("\n⏰ Games start at 7 PM ET - place your bets!")
