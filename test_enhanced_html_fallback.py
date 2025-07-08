"""
Test the enhanced HTML fallback in PrizePicks client
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from odds_provider.prizepicks import PrizePicksClient
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_html_fallback():
    """Test the HTML fallback directly"""
    client = PrizePicksClient()
    
    print("\n=== Testing Enhanced HTML Fallback ===")
    
    # Test WNBA
    print("\nTesting WNBA...")
    slips = client.fetch_html_fallback("WNBA")
    print(f"Fetched {len(slips)} WNBA projections")
    
    if slips:
        print("\nFirst 3 WNBA projections:")
        for i, slip in enumerate(slips[:3]):
            print(f"\n{i+1}. {slip.get('player_name')} ({slip.get('player_team')})")
            print(f"   {slip.get('stat_type')}: {slip.get('line_score')}")
            print(f"   vs {slip.get('opponent')}")
    
    # Test MLB
    print("\n\nTesting MLB...")
    mlb_slips = client.fetch_html_fallback("MLB")
    print(f"Fetched {len(mlb_slips)} MLB projections")
    
    return len(slips) > 0

def test_full_fetch_with_fallback():
    """Test the full fetch_current_board with fallback"""
    client = PrizePicksClient()
    
    print("\n=== Testing Full Fetch (API + Fallback) ===")
    
    csv_path, slips = client.fetch_current_board("data", "WNBA")
    print(f"\nTotal slips fetched: {len(slips)}")
    print(f"CSV saved to: {csv_path}")
    
    if slips:
        print("\nSample slip structure:")
        import json
        print(json.dumps(slips[0], indent=2))

if __name__ == "__main__":
    # Test HTML fallback
    success = test_html_fallback()
    
    # Test full fetch
    test_full_fetch_with_fallback()
    
    print("\n✅ Tests completed!" if success else "\n❌ Tests failed!")
