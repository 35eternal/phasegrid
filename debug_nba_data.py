from odds_provider.prizepicks import PrizePicksClient
import json

# Fetch NBA data
client = PrizePicksClient()
csv_path, board_data = client.fetch_current_board(output_dir="data", league="NBA")

print(f"Fetched {len(board_data)} NBA props")

if board_data:
    # Check first few props
    print("\nFirst 3 NBA props:")
    for i, prop in enumerate(board_data[:3]):
        print(f"\nProp {i+1}:")
        for key, value in prop.items():
            print(f"  {key}: {value}")
    
    # Check for confidence field
    has_confidence = any('confidence' in prop for prop in board_data)
    print(f"\nHas confidence field: {has_confidence}")
    
    # Check what fields are present
    all_keys = set()
    for prop in board_data:
        all_keys.update(prop.keys())
    print(f"\nAll fields in NBA data: {sorted(all_keys)}")
