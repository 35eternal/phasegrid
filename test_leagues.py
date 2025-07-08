from odds_provider.prizepicks import PrizePicksClient
import json

client = PrizePicksClient()

# Test different leagues
leagues = ["NBA", "WNBA", "MLB", "NFL", "NHL", "PGA", "CFB", "CBB"]

for league in leagues:
    try:
        csv_path, board_data = client.fetch_current_board(output_dir="data", league=league)
        if board_data:
            print(f"✅ {league}: {len(board_data)} props available")
            # Show one example
            prop = board_data[0]
            print(f"   Example: {prop.get('player')} - {prop.get('prop_type')}")
        else:
            print(f"❌ {league}: No props found")
    except Exception as e:
        print(f"❌ {league}: Error - {str(e)[:50]}")
