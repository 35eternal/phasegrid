import requests
import time
import json
import pandas as pd
from typing import Dict, List, Optional

BASE_URL = "https://api.prizepicks.com/projections"
PLAYERS_URL = "https://api.prizepicks.com/players"
OUTPUT_FILE = "data/wnba_prizepicks_props.json"

HEADERS = {
    "Accept": "application/json",
    "Origin": "https://app.prizepicks.com",
    "Referer": "https://app.prizepicks.com/",
    "User-Agent": "Mozilla/5.0"
}

COOKIES = {
    "_prizepicks_session": "YOUR_SESSION_COOKIE_HERE",  # Replace this
    # You can copy others too if needed
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

def fetch_player_details(player_ids: List[str]) -> Dict[str, Dict]:
    """
    Fetch player names and details for given player IDs
    
    Args:
        player_ids: List of player ID strings
        
    Returns:
        Dict mapping player_id -> player_info
    """
    print(f"🔍 Fetching details for {len(player_ids)} unique players...")
    
    player_info = {}
    
    # Method 1: Try bulk fetch (if API supports it)
    try:
        # Some APIs allow comma-separated IDs
        ids_param = ",".join(player_ids)
        response = requests.get(
            PLAYERS_URL,
            headers=HEADERS,
            cookies=COOKIES,
            params={"ids": ids_param}
        )
        
        if response.status_code == 200:
            data = response.json()
            players = data.get("data", [])
            
            for player in players:
                player_id = str(player.get("id"))
                attributes = player.get("attributes", {})
                
                player_info[player_id] = {
                    "name": attributes.get("name", "Unknown"),
                    "display_name": attributes.get("display_name", "Unknown"),
                    "team": attributes.get("team", ""),
                    "position": attributes.get("position", ""),
                    "league": attributes.get("league", "")
                }
            
            print(f"✅ Bulk fetch successful: {len(player_info)} players")
            return player_info
            
    except Exception as e:
        print(f"⚠️ Bulk fetch failed: {e}")
    
    # Method 2: Individual fetches (fallback)
    print("📡 Falling back to individual player fetches...")
    
    for player_id in player_ids:
        try:
            response = requests.get(
                f"{PLAYERS_URL}/{player_id}",
                headers=HEADERS,
                cookies=COOKIES
            )
            
            if response.status_code == 200:
                data = response.json()
                player_data = data.get("data", {})
                attributes = player_data.get("attributes", {})
                
                player_info[player_id] = {
                    "name": attributes.get("name", "Unknown"),
                    "display_name": attributes.get("display_name", "Unknown"),
                    "team": attributes.get("team", ""),
                    "position": attributes.get("position", ""),
                    "league": attributes.get("league", "")
                }
                
            else:
                print(f"⚠️ Failed to fetch player {player_id}: {response.status_code}")
                player_info[player_id] = {
                    "name": f"Unknown_Player_{player_id}",
                    "display_name": f"Unknown_Player_{player_id}",
                    "team": "",
                    "position": "",
                    "league": ""
                }
            
            # Rate limiting
            time.sleep(0.1)
            
        except Exception as e:
            print(f"⚠️ Error fetching player {player_id}: {e}")
            player_info[player_id] = {
                "name": f"Error_Player_{player_id}",
                "display_name": f"Error_Player_{player_id}",
                "team": "",
                "position": "",
                "league": ""
            }
    
    print(f"✅ Individual fetch complete: {len(player_info)} players")
    return player_info

def scrape_wnba_props():
    """Enhanced scraper that includes player name resolution"""
    print("🏀 Scraping PrizePicks WNBA props with player names...\n")
    
    page = 1
    all_props = []
    all_player_ids = set()
    
    # Step 1: Collect all projections and player IDs
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
            
        # Process projections and collect player IDs
        for proj in projections:
            proj_data = {
                "projection_id": proj.get("id"),
                "player_id": proj.get("relationships", {}).get("new_player", {}).get("data", {}).get("id"),
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
            
            # Collect unique player IDs
            if proj_data["player_id"]:
                all_player_ids.add(str(proj_data["player_id"]))
            
            all_props.append(proj_data)
        
        print(f"✅ Page {page}: {len(projections)} projections")
        page += 1
        
        # Rate limiting
        time.sleep(0.5)
    
    print(f"\n📊 Total projections: {len(all_props)}")
    print(f"👥 Unique players: {len(all_player_ids)}")
    
    # Step 2: Fetch player details
    player_info = fetch_player_details(list(all_player_ids))
    
    # Step 3: Merge player names into projections
    enriched_props = []
    for prop in all_props:
        player_id = str(prop["player_id"]) if prop["player_id"] else None
        
        if player_id and player_id in player_info:
            prop.update({
                "player_name": player_info[player_id]["name"],
                "display_name": player_info[player_id]["display_name"],
                "team": player_info[player_id]["team"],
                "position": player_info[player_id]["position"]
            })
        else:
            prop.update({
                "player_name": "Unknown",
                "display_name": "Unknown", 
                "team": "",
                "position": ""
            })
        
        enriched_props.append(prop)
    
    # Step 4: Save enriched data
    print(f"\n💾 Saving {len(enriched_props)} enriched projections...")
    
    # Save as JSON
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(enriched_props, f, indent=2)
    
    # Save as CSV for easy analysis
    df = pd.DataFrame(enriched_props)
    csv_file = OUTPUT_FILE.replace('.json', '.csv')
    df.to_csv(csv_file, index=False)
    
    print(f"✅ Saved to {OUTPUT_FILE}")
    print(f"✅ Saved to {csv_file}")
    
    # Display sample with names
    print(f"\n🔍 Sample projections with player names:")
    sample_df = df[['player_name', 'team', 'stat_type', 'line_score']].head(10)
    print(sample_df.to_string(index=False))
    
    return enriched_props

def get_unique_player_names() -> List[str]:
    """Extract unique player names from saved props for mapping"""
    try:
        df = pd.read_csv(OUTPUT_FILE.replace('.json', '.csv'))
        unique_names = df['player_name'].dropna().unique().tolist()
        return [name for name in unique_names if name != "Unknown"]
    except Exception as e:
        print(f"Error reading saved props: {e}")
        return []

if __name__ == "__main__":
    props = scrape_wnba_props()
    
    # Show unique players for mapping
    unique_players = get_unique_player_names()
    print(f"\n👥 Unique players found ({len(unique_players)}):")
    for name in sorted(unique_players):
        print(f"  - {name}")
    
    print(f"\n🔗 Next step: Run player mapping on these {len(unique_players)} names")