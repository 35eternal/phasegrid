#!/usr/bin/env python3
"""
Rate-limit aware PrizePicks scraper with fallback options
"""

import json
import time
import httpx
from pathlib import Path
from datetime import datetime, timedelta
import random

class PrizePicksScraper:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        # Multiple API endpoints to try
        self.endpoints = [
            "https://api.prizepicks.com/projections",
            "https://partner.prizepicks.com/projections/basketball/nba",
            "https://api.prizepicks.com/projections?league_id=3",
            "https://api.prizepicks.com/projections?single_stat=true&league_id=3"
        ]
        
        # Headers rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        
    def get_headers(self):
        """Rotate headers to avoid detection"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://app.prizepicks.com/',
            'Origin': 'https://app.prizepicks.com',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        }
        
    def fetch_with_retry(self):
        """Fetch data with retry logic and rate limit handling"""
        
        for endpoint in self.endpoints:
            try:
                print(f"🔄 Trying: {endpoint}")
                
                # Add delay between requests
                time.sleep(random.uniform(2, 5))
                
                with httpx.Client(timeout=30) as client:
                    response = client.get(endpoint, headers=self.get_headers())
                    
                    if response.status_code == 200:
                        print("✅ Success!")
                        return response.json()
                        
                    elif response.status_code == 429:
                        print("⚠️ Rate limited on this endpoint")
                        continue
                        
                    else:
                        print(f"❌ Status {response.status_code}")
                        
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
                
        return None
        
    def check_existing_data(self):
        """Check for existing data files"""
        print("\n📂 Checking existing data files...")
        
        patterns = [
            "*prizepicks*.csv",
            "*prizepicks*.json",
            "*props*.csv",
            "*props*.json"
        ]
        
        found_files = []
        for pattern in patterns:
            found_files.extend(self.data_dir.glob(pattern))
            
        if found_files:
            print("\n✅ Found existing files:")
            for file in sorted(found_files, key=lambda x: x.stat().st_mtime, reverse=True):
                mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                age = datetime.now() - mod_time
                print(f"  - {file.name} (modified {age.days} days ago)")
                
            # Use most recent file if it's less than 24 hours old
            newest = max(found_files, key=lambda x: x.stat().st_mtime)
            if (datetime.now() - datetime.fromtimestamp(newest.stat().st_mtime)) < timedelta(hours=24):
                print(f"\n💡 Using recent data from: {newest.name}")
                return newest
                
        return None
        
    def use_mock_data(self):
        """Create mock data for testing when rate limited"""
        print("\n🎭 Creating mock WNBA data for testing...")
        
        mock_props = [
            {"player_name": "A'ja Wilson", "team_name": "Las Vegas Aces", "stat_type": "Points", "line": 23.5},
            {"player_name": "Breanna Stewart", "team_name": "New York Liberty", "stat_type": "Rebounds", "line": 8.5},
            {"player_name": "Napheesa Collier", "team_name": "Minnesota Lynx", "stat_type": "Pts+Rebs+Asts", "line": 35.5},
            {"player_name": "Alyssa Thomas", "team_name": "Connecticut Sun", "stat_type": "Assists", "line": 6.5},
            {"player_name": "Kahleah Copper", "team_name": "Phoenix Mercury", "stat_type": "Points", "line": 18.5},
        ]
        
        # Add timestamp
        for prop in mock_props:
            prop["timestamp"] = datetime.now().isoformat()
            
        # Save mock data
        mock_file = self.data_dir / "mock_wnba_props.json"
        with open(mock_file, 'w') as f:
            json.dump(mock_props, f, indent=2)
            
        print(f"✅ Saved mock data to: {mock_file}")
        return mock_props
        
    def run(self):
        """Main execution"""
        print("🏀 PrizePicks WNBA Scraper (Rate-Limit Aware)")
        print("=" * 50)
        
        # First check for existing recent data
        existing = self.check_existing_data()
        if existing:
            print("\n✅ Using existing recent data!")
            return
            
        # Try to fetch new data
        data = self.fetch_with_retry()
        
        if data:
            # Parse and save the data
            # (parsing logic would go here based on actual API structure)
            print("✅ Successfully fetched new data!")
            
        else:
            print("\n⚠️ Could not fetch data due to rate limiting")
            print("\n🔧 Options:")
            print("1. Wait 30-60 minutes for rate limit to reset")
            print("2. Use existing data files if available")
            print("3. Use mock data for testing")
            
            # Create mock data for testing
            self.use_mock_data()
            
            print("\n💡 Tips to avoid rate limiting:")
            print("- Don't run scrapers too frequently")
            print("- Add delays between requests")
            print("- Use a VPN or proxy to change IP")
            print("- Cache data and reuse when possible")


if __name__ == "__main__":
    scraper = PrizePicksScraper()
    scraper.run()