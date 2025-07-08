import os
import sys
sys.path.insert(0, os.getcwd())

from odds_provider.prizepicks import PrizePicksClient
import time
import logging

logging.basicConfig(level=logging.DEBUG)

# Test with enhanced headers that mimic a real browser
class EnhancedPrizePicksClient(PrizePicksClient):
    def __init__(self):
        super().__init__()
        # Override headers to be more browser-like
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": "https://prizepicks.com",
            "Referer": "https://prizepicks.com/",
            "Sec-Ch-Ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "\"Windows\"",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        })
        # Remove Authorization header since API doesn't use it
        self.session.headers.pop("Authorization", None)

# Test the enhanced client
client = EnhancedPrizePicksClient()
try:
    print("Testing API with enhanced headers...")
    data = client.fetch_projections(league="WNBA")
    slips = client.parse_projections_to_slips(data)
    print(f"Success! Fetched {len(slips)} projections via API")
except Exception as e:
    print(f"API failed: {e}")
    print("\nTrying HTML fallback...")
    slips = client.fetch_html_fallback("WNBA")
    print(f"HTML returned {len(slips)} projections")
