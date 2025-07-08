from odds_provider.prizepicks import fetch_current_board
import json

try:
    board = fetch_current_board()
    print(f"Fetched {len(board)} props")
    if board:
        # Show first 3 props
        for i, prop in enumerate(board[:3]):
            print(f"\nProp {i+1}:")
            print(json.dumps(prop, indent=2))
except Exception as e:
    print(f"Error fetching board: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
