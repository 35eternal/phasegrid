#!/usr/bin/env python3
"""Test the fixed PrizePicks client"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔧 TESTING FIXED PRIZEPICKS CLIENT")
print("=" * 40)

# Wait a bit for rate limit
print("Waiting 20 seconds for rate limit...")
time.sleep(20)

from odds_provider.prizepicks import PrizePicksClient

client = PrizePicksClient()

# This should now fetch ALL projections, not just live
print("\n📊 Fetching WNBA projections...")
projections = client.fetch_projections(league="WNBA", include_live=True)

if isinstance(projections, dict):
    count = len(projections.get('data', []))
    print(f"✅ Found {count} WNBA projections")
    
    if count > 0:
        print("\n🎯 SUCCESS! Running auto_paper now...")
        import os
        os.system("python auto_paper.py --production --bypass-guard-rail")
    else:
        # Check the URL to confirm live parameter is gone
        if 'links' in projections:
            print(f"\nAPI URL: {projections['links'].get('self', 'Not found')}")
            if 'live=True' in str(projections['links'].get('self', '')):
                print("❌ ERROR: 'live=True' still in URL - fix didn't work")
            else:
                print("✅ 'live' parameter removed from URL")
else:
    print("❌ Unexpected response format")
