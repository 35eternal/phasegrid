from data_transformer import transform_board_data
from slip_optimizer import build_slips
from odds_provider.prizepicks import PrizePicksClient

# Fetch NBA data
client = PrizePicksClient()
csv_path, board_data = client.fetch_current_board(output_dir="data", league="NBA")

print(f"Original props: {len(board_data)}")

# Transform the data
transformed = transform_board_data(board_data)
print(f"Transformed bets: {len(transformed)}")

# Check a transformed bet
if transformed:
    print("\nSample transformed bet:")
    for key, value in transformed[0].items():
        print(f"  {key}: {value}")

# Try to build slips
try:
    slips = build_slips(transformed[:200], target_count=10, bypass_guard_rail=True)  # Use subset to avoid long processing
    print(f"\n✅ Generated {len(slips)} slips from NBA/MLB data!")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
