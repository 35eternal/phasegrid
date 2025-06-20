import requests
import time
import json
import pandas as pd
from typing import Dict, Optional

BASE_URL = "https://api.prizepicks.com/projections"
PLAYER_URL = "https://api.prizepicks.com/players"
OUTPUT_FILE = "data/wnba_prizepicks_props.json"

HEADERS = {
    "Accept": "application/json",
    "Origin": "https://app.prizepicks.com",
    "Referer": "https://app.prizepicks.com/",
    "User-Agent": "Mozilla/5.0"
}

COOKIES = {
    "_prizepicks_session": "YOUR_SESSION_COOKIE_HERE",  # Replace this
}

PARAMS = {
    "league_id": 3,
    "page": 1,
    "per_page": 250,
    "single_stat": "true",
    "in_game": "true",
    "state_code": "NM",
    "game_mode": "pickem"
}

def fetch_player_name(player_id: str) -> Optional[Dict]:
    """
    Fetch individual player details - simple and reliable
    
    Args:
        player_id: Player ID string
        
    Returns:
        Dict with player info or None
    """
    try:
        response = requests.get(
            f"{PLAYER_URL}/{player_id}",
            headers=HEADERS,
            cookies=COOKIES,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            player_data = data.get("data", {})
            attributes = player_data.get("attributes", {})
            
            return {
                "name": attributes.get("name", f"Player_{player_id}"),
                "team": attributes.get("team", ""),
                "position": attributes.get("position", ""),
                "team_name": attributes.get("team_name", "")
            }
        else:
            print(f"⚠️ Player {player_id}: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Player {player_id}: {e}")
        return None

def scrape_wnba_props_simple():
    """Simple scraper that fetches player names on-the-fly"""
    print("🏀 Scraping PrizePicks WNBA props (Simple & Reliable)...\n")
    
    page = 1
    all_props = []
    player_cache = {}  # Cache to avoid duplicate API calls
    
    # Scrape projections page by page
    while True:
        PARAMS["page"] = page
        response = requests.get(BASE_URL, headers=HEADERS, cookies=COOKIES, params=PARAMS)
        
        if response.status_code == 429:
            print(f"⌛ Page {page}: Rate limited. Stopping scrape.")
            break
            
        if response.status_code != 200:
            print(f"❌ Page {page}: Failed to fetch - {response.status_code}")
            break
        
        data = response.json()
        projections = data.get("data", [])
        
        if not projections:
            print(f"📄 Page {page}: No more projections found")
            break
        
        print(f"📄 Page {page}: Processing {len(projections)} projections...")
        
        # Process each projection
        for i, proj in enumerate(projections):
            # Extract basic projection data
            player_id = proj.get("relationships", {}).get("new_player", {}).get("data", {}).get("id")
            
            proj_data = {
                "projection_id": proj.get("id"),
                "player_id": player_id,
                "game_id": proj.get("relationships", {}).get("game", {}).get("data", {}).get("id"),
                "stat_type": proj["attributes"].get("stat_type"),
                "line_score": proj["attributes"].get("line_score"),
                "start_time": proj["attributes"].get("start_time"),
                "updated_at": proj["attributes"].get("updated_at"),
                "status": proj["attributes"].get("status"),
                "odds_type": proj["attributes"].get("odds_type"),
                "is_live": proj["attributes"].get("is_live"),
                "is_promo": proj["attributes"].get("is_promo")
            }
            
            # Fetch player name if we have a player_id
            if player_id:
                if player_id not in player_cache:
                    print(f"  🔍 Fetching player {player_id}...")
                    player_info = fetch_player_name(player_id)
                    player_cache[player_id] = player_info
                    time.sleep(0.2)  # Rate limiting
                
                # Add player info to projection
                player_info = player_cache[player_id]
                if player_info:
                    proj_data.update({
                        "player_name": player_info["name"],
                        "team": player_info["team"],
                        "position": player_info["position"],
                        "team_name": player_info["team_name"]
                    })
                else:
                    proj_data.update({
                        "player_name": f"Unknown_{player_id}",
                        "team": "",
                        "position": "",
                        "team_name": ""
                    })
            else:
                proj_data.update({
                    "player_name": "No_Player_ID",
                    "team": "",
                    "position": "",
                    "team_name": ""
                })
            
            all_props.append(proj_data)
        
        print(f"✅ Page {page}: {len(projections)} projections processed")
        page += 1
        
        # Rate limiting between pages
        time.sleep(1)
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"📋 Total projections: {len(all_props)}")
    print(f"👥 Unique players: {len(player_cache)}")
    
    # Show player cache
    print(f"\n👥 Players found:")
    for player_id, info in player_cache.items():
        if info:
            name = info["name"]
            team = info["team"]
            print(f"  {player_id}: {name} ({team})")
        else:
            print(f"  {player_id}: Failed to fetch")
    
    # Save data
    print(f"\n💾 Saving data...")
    
    # Save as JSON
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(all_props, f, indent=2)
    
    # Save as CSV
    df = pd.DataFrame(all_props)
    csv_file = OUTPUT_FILE.replace('.json', '.csv')
    df.to_csv(csv_file, index=False)
    
    print(f"✅ Saved to {OUTPUT_FILE}")
    print(f"✅ Saved to {csv_file}")
    
    # Show sample with names
    print(f"\n🔍 Sample projections with player names:")
    if len(all_props) > 0:
        sample_df = df[['player_name', 'team', 'stat_type', 'line_score']].head(10)
        print(sample_df.to_string(index=False))
    
    # Extract unique names for mapping
    unique_names = df[df['player_name'].notna()]['player_name'].unique()
    valid_names = [name for name in unique_names if not name.startswith(('Unknown_', 'No_Player'))]
    
    print(f"\n🎯 Ready for mapping: {len(valid_names)} valid player names")
    for name in sorted(valid_names):
        print(f"  - {name}")
    
    return all_props

if __name__ == "__main__":
    props = scrape_wnba_props_simple()
    print(f"\n🔗 Next: Run your existing player mapper on these names!")