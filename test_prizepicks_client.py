from odds_provider.prizepicks import PrizePicksClient
import json
from datetime import datetime

try:
    client = PrizePicksClient()
    csv_path, board_data = client.fetch_current_board(output_dir="data", league="NBA")
    
    print(f"CSV saved to: {csv_path}")
    print(f"Fetched {len(board_data)} props")
    
    if board_data:
        # Show first 3 props
        for i, prop in enumerate(board_data[:3]):
            print(f"\nProp {i+1}:")
            print(json.dumps(prop, indent=2, default=str))
    else:
        print("No props found!")
        
    # Check if it's test data
    if board_data and 'TestPlayer' in str(board_data[0]):
        print("\n⚠️ WARNING: This appears to be TEST DATA!")
        
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
