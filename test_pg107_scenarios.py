"""
Test PG-107: Enhanced HTML Scraping for dry-run scenarios
"""
from odds_provider.prizepicks import PrizePicksClient
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

def test_fallback_scenarios():
    """Test various fallback scenarios"""
    client = PrizePicksClient()
    
    print("🧪 PG-107: Testing Enhanced HTML Fallback Scenarios\n")
    
    # Scenario 1: Direct HTML fallback call
    print("📋 Scenario 1: Direct HTML fallback")
    print("-" * 50)
    wnba_slips = client.fetch_html_fallback("WNBA")
    print(f"✅ WNBA: {len(wnba_slips)} projections")
    
    mlb_slips = client.fetch_html_fallback("MLB")
    print(f"✅ MLB: {len(mlb_slips)} projections")
    
    # Scenario 2: Full fetch (should use main API)
    print("\n📋 Scenario 2: Full fetch with automatic fallback")
    print("-" * 50)
    csv_path, all_slips = client.fetch_current_board("data", "WNBA")
    print(f"✅ Total slips: {len(all_slips)}")
    print(f"✅ CSV saved: {csv_path}")
    
    # Show sample data
    if all_slips:
        print("\n📊 Sample projections:")
        for i, slip in enumerate(all_slips[:3]):
            print(f"\n{i+1}. {slip.get('player', 'Unknown')} ({slip.get('team', 'N/A')})")
            print(f"   {slip.get('prop_type', 'Unknown')}: {slip.get('line', 0)}")
    
    return len(wnba_slips) > 0 or len(all_slips) > 0

if __name__ == "__main__":
    success = test_fallback_scenarios()
    print("\n" + "="*50)
    print("🎉 PG-107 COMPLETE!" if success else "❌ PG-107 FAILED!")
    print("="*50)
