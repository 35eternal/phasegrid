#!/usr/bin/env python3
"""Check what sports have data available"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from odds_provider.prizepicks import PrizePicksClient
import json

print("🔍 Checking ALL available sports on PrizePicks...")

client = PrizePicksClient()

# Try different leagues
leagues = ["WNBA", "NBA", "NFL", "MLB", "NHL", "UFC", "SOCCER"]

for league in leagues:
    try:
        projections = client.fetch_projections(league=league, include_live=True)
        count = len(projections.get('data', [])) if isinstance(projections, dict) else 0
        print(f"{league}: {count} projections")
    except Exception as e:
        print(f"{league}: Error - {e}")
