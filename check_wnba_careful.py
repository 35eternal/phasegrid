#!/usr/bin/env python3
"""Check WNBA lines with rate limit protection"""
import time
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from odds_provider.prizepicks import PrizePicksClient

print("🏀 RATE-LIMITED WNBA CHECK")
print("Waiting 30 seconds to respect rate limits...")
time.sleep(30)  # Wait to avoid rate limit

try:
    client = PrizePicksClient()
    projections = client.fetch_projections(league="WNBA", include_live=True)
    
    if isinstance(projections, dict):
        count = len(projections.get('data', []))
        print(f"\n✅ WNBA projections available: {count}")
        
        if count > 0:
            print("🚨 LINES ARE LIVE! Running full pipeline...")
            os.system("python auto_paper.py --dry-run --bypass-guard-rail")
    else:
        print("❌ Unexpected response format")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("⏰ Will retry in next scheduled check")
