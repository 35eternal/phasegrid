#!/usr/bin/env python3
"""Check what PrizePicks data we're receiving - FIXED"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from odds_provider.prizepicks import PrizePicksClient
from datetime import datetime
import json

print("🔍 Fetching current PrizePicks projections...")

# Initialize the client
client = PrizePicksClient()

# Fetch projections - NOT just live ones
projections = client.fetch_projections(league_id=7, live=False)
print(f"\n📊 Found {len(projections)} total projections")

# Also try fetching without live parameter
all_projections = client.fetch_projections(league_id=7)
print(f"📊 Found {len(all_projections)} projections (without live filter)")

# Show sample data
if projections:
    print("\n📋 First 3 projections:")
    for i, proj in enumerate(projections[:3]):
        print(f"\n--- Projection {i+1} ---")
        player_info = proj.get('attributes', {}).get('new_player', {})
        print(f"Player: {player_info.get('name', 'Unknown')}")
        print(f"Stat: {proj.get('attributes', {}).get('stat_type', 'Unknown')}")
        print(f"Line: {proj.get('attributes', {}).get('line_score', 'N/A')}")
        
# Check dates
print("\n📅 Checking game dates...")
dates = set()
for proj in projections[:20]:
    game_time = proj.get('attributes', {}).get('game', {}).get('start_time', '')
    if game_time:
        dates.add(game_time[:10])
        
print(f"Game dates found: {sorted(dates)}")

# Save debug data
with open('prizepicks_debug.json', 'w') as f:
    json.dump(projections[:3], f, indent=2, default=str)
print("\n💾 Saved debug data to prizepicks_debug.json")
