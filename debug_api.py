#!/usr/bin/env python3
"""Debug PrizePicks API parameters"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from odds_provider.prizepicks import PrizePicksClient
import json

print("🔍 DEBUGGING PRIZEPICKS API")
print("=" * 40)

# Check the client configuration
client = PrizePicksClient()

# Print the league mapping
print("\n📊 League mappings:")
if hasattr(client, 'LEAGUE_IDS'):
    for league, id in client.LEAGUE_IDS.items():
        print(f"  {league}: {id}")

# Check the actual URL being called
print("\n🌐 API Details:")
print(f"Base URL: {client.BASE_URL}")
print(f"Endpoint: {client.PROJECTIONS_ENDPOINT}")

# Try different parameter combinations
test_params = [
    {"league": "WNBA", "include_live": True},
    {"league": "WNBA", "include_live": False},
    {"league": "wnba", "include_live": True},  # lowercase
    {"league": 7, "include_live": True},       # direct league ID
]

print("\n🧪 Testing different parameter combinations:")
for params in test_params:
    print(f"\nTrying: {params}")
    try:
        # Build the URL manually to see what's being called
        league_param = params.get('league')
        if isinstance(league_param, str) and hasattr(client, 'LEAGUE_IDS'):
            league_id = client.LEAGUE_IDS.get(league_param.upper(), league_param)
        else:
            league_id = league_param
            
        print(f"  League ID used: {league_id}")
        
        # You might need to check the actual request URL
    except Exception as e:
        print(f"  Error: {e}")

# Look for the URL in the response
print("\n📝 Checking last API response:")
projections = client.fetch_projections(league="WNBA", include_live=True)
if isinstance(projections, dict) and 'links' in projections:
    print(f"API URL used: {projections['links'].get('self', 'Not found')}")
