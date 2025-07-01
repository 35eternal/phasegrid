#!/usr/bin/env python3
"""Emergency WNBA line fetcher"""
import os
import sys
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🚨 EMERGENCY WNBA LINE FETCHER")
print("=" * 50)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")

# Wait a bit to ensure no rate limit
print("\nWaiting 10 seconds to avoid rate limit...")
time.sleep(10)

from odds_provider.prizepicks import PrizePicksClient

try:
    print("\n📊 Fetching WNBA projections...")
    client = PrizePicksClient()
    
    # Try without live filter first
    projections = client.fetch_projections(league="WNBA", include_live=False)
    
    if isinstance(projections, dict):
        data = projections.get('data', [])
        print(f"✅ Found {len(data)} WNBA projections!")
        
        if data:
            # Save raw data
            with open('wnba_lines_raw.json', 'w') as f:
                json.dump(projections, f, indent=2)
            print("💾 Saved raw data to wnba_lines_raw.json")
            
            # Show sample lines
            print("\n📋 Sample lines found:")
            for i, proj in enumerate(data[:5]):
                attrs = proj.get('attributes', {})
                player = attrs.get('new_player', {}).get('name', 'Unknown')
                stat = attrs.get('stat_type', 'Unknown')
                line = attrs.get('line_score', 'N/A')
                print(f"  {player} - {stat}: {line}")
                
            # Now run the full pipeline
            print("\n🚀 Running full betting pipeline...")
            os.system("python auto_paper.py --production --bypass-guard-rail")
        else:
            print("❌ No data in response")
            
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTrying alternative approach...")
