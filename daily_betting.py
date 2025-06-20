from modules.sheet_connector import BetSyncSheetConnector
from datetime import datetime
import json

# Helper function to safely convert values
def safe_float(value, default=0):
    """Convert value to float, handling empty strings and None"""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

# Initialize connection
sheet = BetSyncSheetConnector()

# Check if we're in test mode
print("=== BETTING MODE SELECTION ===")
mode = input("Enter mode (REAL/TEST) [default: REAL]: ").strip().upper()
if mode not in ['REAL', 'TEST']:
    mode = 'REAL'

is_test_mode = (mode == 'TEST')
mode_prefix = "TEST_" if is_test_mode else ""

print(f"\n{'='*50}")
print(f"RUNNING IN {mode} MODE")
if is_test_mode:
    print("⚠️  TEST MODE - Bets will be marked as tests")
print(f"{'='*50}")

# Read current settings
settings = sheet.read_settings()
bankroll = safe_float(settings.get('bankroll', 1000))
kelly_divisor = safe_float(settings.get('kelly_divisor', 4))
max_bets = int(safe_float(settings.get('max_bets_per_day', 10)))

print(f"\n=== DAILY BETTING SYSTEM ===")
print(f"Current bankroll: ${bankroll:.2f}")
print(f"Kelly divisor: {kelly_divisor}")
print(f"Max bets today: {max_bets}")

# Example: Your prediction system generates these
# TODO: Replace this with your actual WNBA prediction model output
predictions = [
    {
        'player': 'A\'ja Wilson',
        'market': 'points_over',
        'line': 24.5,
        'prediction': 27.2,
        'edge': 0.082,  # 8.2% edge
        'phase': 'high_confidence',
        'odds': 1.91
    },
    {
        'player': 'Napheesa Collier',
        'market': 'rebounds_over',
        'line': 8.5,
        'prediction': 9.8,
        'edge': 0.065,
        'phase': 'medium_confidence',
        'odds': 1.87
    },
    {
        'player': 'Kelsey Plum',
        'market': 'assists_over',
        'line': 5.5,
        'prediction': 6.3,
        'edge': 0.045,
        'phase': 'low_confidence',
        'odds': 1.95
    }
]

print(f"\n=== TODAY'S PREDICTIONS ===")
print(f"Found {len(predictions)} betting opportunities")

# Calculate bet sizes using Kelly criterion
bets_to_place = []
for i, pred in enumerate(predictions[:max_bets]):
    # Kelly formula: f = (p*b - q) / b
    # Simplified: f = edge / kelly_divisor
    kelly_fraction = pred['edge'] / kelly_divisor
    bet_size = round(bankroll * kelly_fraction, 2)
    
    # In test mode, use smaller amounts
    if is_test_mode:
        bet_size = min(bet_size, 25.00)  # Cap test bets at $25
    
    # Cap at 5% of bankroll for safety
    max_bet_size = round(bankroll * 0.05, 2)
    if bet_size > max_bet_size:
        print(f"  Capping bet size at 5% of bankroll (${max_bet_size})")
        bet_size = max_bet_size
    
    # Minimum bet size check
    min_bet = 5 if is_test_mode else 10
    if bet_size < min_bet:
        print(f"  Skipping {pred['player']} - bet size too small (${bet_size:.2f})")
        continue
    
    bet = {
        'source_id': f"{mode_prefix}WNBA_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i:02d}_{pred['player'].replace(' ', '_')}",
        'timestamp': datetime.now().isoformat(),
        'player_name': pred['player'],
        'market': pred['market'],
        'line': pred['line'],
        'phase': pred['phase'],
        'adjusted_prediction': pred['prediction'],
        'wager_amount': bet_size,
        'odds': pred['odds'],
        'notes': f"{'TEST BET - ' if is_test_mode else ''}Edge: {pred['edge']*100:.1f}%, Pred: {pred['prediction']}"
    }
    bets_to_place.append(bet)
    
    print(f"\nBet #{len(bets_to_place)}:")
    print(f"  Player: {pred['player']}")
    print(f"  Market: {pred['market']} {pred['line']}")
    print(f"  Prediction: {pred['prediction']} (edge: {pred['edge']*100:.1f}%)")
    print(f"  Phase: {pred['phase']}")
    print(f"  Wager: ${bet_size:.2f} @ {pred['odds']}")
    if is_test_mode:
        print(f"  ⚠️  TEST BET")

# Confirm before placing
if bets_to_place:
    print(f"\n=== SUMMARY ===")
    print(f"MODE: {'TEST' if is_test_mode else 'REAL'} BETTING")
    total_wager = sum(bet['wager_amount'] for bet in bets_to_place)
    print(f"Total bets: {len(bets_to_place)}")
    print(f"Total wager: ${total_wager:.2f}")
    print(f"Remaining bankroll: ${bankroll - total_wager:.2f}")
    
    confirm = input(f"\nPlace these {'TEST' if is_test_mode else 'REAL'} bets? (y/n): ").strip().lower()
    
    if confirm == 'y':
        # Write to sheet
        written, skipped = sheet.write_new_bets(bets_to_place)
        print(f"\n✅ SUCCESS: Placed {written} {'TEST' if is_test_mode else 'REAL'} bets")
        if skipped > 0:
            print(f"⚠️  Skipped {skipped} duplicate bets")
            
        # Show bet IDs for tracking
        print(f"\n{'Test' if is_test_mode else 'Bet'} IDs for tracking:")
        for bet in bets_to_place[:written]:
            print(f"  {bet['source_id']}")
    else:
        print("\n❌ Betting cancelled")
else:
    print("\n⚠️  No bets meet criteria for today")

print("\nUse 'python update_results.py' after games to update results")