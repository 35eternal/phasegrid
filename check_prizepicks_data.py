#!/usr/bin/env python3
"""Check what PrizePicks data we're receiving"""
from odds_provider.prizepicks import PrizePicks
from datetime import datetime
import json

pp = PrizePicks()
print("🔍 Fetching current PrizePicks projections...")

# Fetch all projections
projections = pp.fetch_projections(league_id=7)
print(f"\n📊 Found {len(projections)} total projections")

# Check for WNBA specific
wnba_projections = [p for p in projections if p.get('league', {}).get('name') == 'WNBA']
print(f"🏀 Found {len(wnba_projections)} WNBA projections")

# Show first few projections
if projections:
    print("\n📋 Sample projections:")
    for i, proj in enumerate(projections[:3]):
        print(f"\n--- Projection {i+1} ---")
        print(f"Player: {proj.get('new_player', {}).get('name', 'Unknown')}")
        print(f"Stat: {proj.get('stat_type', {}).get('name', 'Unknown')}")
        print(f"Line: {proj.get('line_score', 'N/A')}")
        print(f"Game Time: {proj.get('game', {}).get('start_time', 'Unknown')}")
        
# Check for today's games
today_games = [p for p in projections if '2025-07-01' in str(p.get('game', {}).get('start_time', ''))]
print(f"\n🎯 Games today (July 1): {len(today_games)}")

# Save full data for inspection
with open('prizepicks_debug.json', 'w') as f:
    json.dump(projections[:5], f, indent=2, default=str)
print("\n💾 Saved sample data to prizepicks_debug.json")
