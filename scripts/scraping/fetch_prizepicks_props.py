﻿# scripts/fetch_prizepicks_props.py
import httpx
import json
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
URL = "https://api.prizepicks.com/projections"
PARAMS = {
    "league_id": "3",
    "per_page": "250",
    "single_stat": "true",
    "in_game": "true",
    "state_code": "NM",
    "game_mode": "pickem"
}
OUTPUT_PATH = Path("data/wnba_prizepicks_props.json")
HEADERS = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.5",
    "content-type": "application/json",
    "if-modified-since": "Thu, 05 Jun 2025 20:22:03 GMT",
    "origin": "https://app.prizepicks.com",
    "priority": "u=1, i",
    "referer": "https://app.prizepicks.com/",
    "sec-ch-ua": "\"Brave\";v=\"137\", \"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "sec-gpc": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "x-device-id": "048c632e-0ed3-4f5e-9cf0-8c938dab0148",
    "x-device-info": "anonymousId=e8c3fcaf-21f9-4815-bedf-1e60e66dc20d,name=,os=windows,osVersion=Windows NT 10.0; Win64; x64,platform=web,appVersion=,gameMode=pickem,stateCode=NM,fbp=fb.1.1748995254414.948797635306132314"
}
COOKIES = {
    "_vwo_uuid_v2": "D17C6965C85DA4524D93A2D00014B5CBE|5a441471879b17e94f5f7151c492c9e7",
    # Include ONLY essential cookies from your working request
    "_prizepicks_session": "kPAf9VeWxP7c2bBVPz%2FNCwpHT9AbQAQ1edBRzj5ITo85vCVbvjHsN0TRNpa8Zwp70VlmrlCaM%2FRVRra8q4DaVOewkzA8%2FvKWjmLuXSfqDWZqPtZiyrTxTVPs3vJ%2FuTl9YerAtKOMVMpF69i4hhoupsfaGhUtI3N5RP4yzr4ae746GYt85nv5D474C9pJG1AGWbwoKnS4mlurpymIRWCMxZZ6AiubP4CYJ7JL2EJeF7NymcRs%2Bq1EgfOJ0kyaMtNm2Q4dCu%2BphjdAvuFV2FI8Fi0aRbkWj8uvcki0UYEtAHSpsCggM%2BGRSVXavp6fGfaK2A%3D%3D--6pB9bSFtVYCmsCgm--vWnK4a8c0X8kXqxzW8tMpQ%3D%3D"
}

# --- Add retry decorator to handle transient failures ---
@retry(
    wait=wait_exponential(multiplier=1, max=30),
    stop=stop_after_attempt(5),
    reraise=True
)
def fetch_with_retry(client, url, params):
    """Fetch data with exponential backoff retry logic."""
    logger.info(f"Attempting to fetch data from {url}")
    response = client.get(url, params=params)
    response.raise_for_status()  # Will raise an error for bad status codes
    return response

# --- Execution ---
def fetch_props():
    print("🔡 Fetching PrizePicks WNBA data...")
    
    try:
        with httpx.Client(headers=HEADERS, cookies=COOKIES, timeout=30) as client:
            response = fetch_with_retry(client, URL, PARAMS)
            
            if response.status_code == 200:
                # Ensure output directory exists
                OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
                
                # Save the response
                data = response.json()
                with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                print(f"✅ Successfully fetched {len(data.get('data', []))} projections")
                print(f"📁 Saved to: {OUTPUT_PATH}")
                
                # Log included items for debugging
                included = data.get('included', [])
                if included:
                    print(f"📊 Additional data: {len(included)} items")
                
                return data
            else:
                logger.error(f"Failed with status code: {response.status_code}")
                return None
                
    except Exception as e:
        logger.error(f"Error fetching PrizePicks data: {str(e)}")
        raise

if __name__ == "__main__":
    fetch_props()
