from odds_provider.prizepicks import PrizePicksClient
import time

print("Waiting 2 seconds between requests to avoid rate limiting...")

client = PrizePicksClient()

# Test 1: Normal fetch
print("\n1. Testing normal API fetch...")
time.sleep(2)
csv_path, slips = client.fetch_current_board("data", "WNBA")
print(f"   Result: {len(slips)} projections fetched")

# Test 2: Direct HTML fallback
print("\n2. Testing HTML fallback directly...")
time.sleep(2)
html_slips = client.fetch_html_fallback("WNBA")
print(f"   Result: {len(html_slips)} projections fetched")

print("\n✅ All tests completed!")
