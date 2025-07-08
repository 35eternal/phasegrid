from odds_provider.prizepicks import PrizePicksClient
import json

client = PrizePicksClient()
csv_path, board_data = client.fetch_current_board(output_dir="data", league="WNBA")

print(f"CSV saved to: {csv_path}")
print(f"Fetched {len(board_data)} WNBA props")

if board_data:
    # Show first 3 WNBA props
    for i, prop in enumerate(board_data[:3]):
        print(f"\nProp {i+1}:")
        print(f"  Player: {prop.get('player')}")
        print(f"  Team: {prop.get('team')}")
        print(f"  Type: {prop.get('prop_type')}")
        print(f"  Line: {prop.get('line')}")
