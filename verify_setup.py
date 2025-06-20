from modules.sheet_connector import BetSyncSheetConnector

# Initialize connector
sheet = BetSyncSheetConnector()

# Check settings
print("\n=== SETTINGS ===")
settings = sheet.read_settings()
for key, value in settings.items():
    print(f"{key}: {value}")

# Check phases  
print("\n=== PHASES ===")
phases = sheet.read_phase_confidence()
for phase in phases:
    print(f"{phase['phase']}: confidence={phase['confidence_level']}")

# Check your bet
print("\n=== YOUR BETS ===")
bets = sheet.get_pending_bets()
print(f"Total pending bets: {len(bets)}")
for bet in bets:
    print(f"Player: {bet['player_name']}, Market: {bet['market']}, Line: {bet['line']}, Wager: ${bet['wager_amount']}")

# Show recent bet history
print("\n=== RECENT BET HISTORY (Last 7 days) ===")
history = sheet.get_bet_history(days_back=7)
print(f"Total bets in last 7 days: {len(history)}")
for bet in history[:5]:  # Show first 5
    status = bet.get('status', 'pending')
    pl = bet.get('profit_loss', 0)
    print(f"{bet['timestamp'][:10]} - {bet['player_name']} {bet['market']} {bet['line']} - Status: {status} - P/L: ${pl}")