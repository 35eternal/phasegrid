from modules.sheet_connector import BetSyncSheetConnector
import json

sheet = BetSyncSheetConnector()

print("=== GOOGLE SHEET STATUS CHECK ===")

# Check bets_log
print("\n1. CHECKING BETS_LOG...")
all_bets = sheet.get_bet_history(days_back=365)
print(f"Total bets found: {len(all_bets)}")

for bet in all_bets:
    print(f"\nBet Details:")
    print(f"  Source ID: {bet.get('source_id', 'N/A')}")
    print(f"  Player: {bet.get('player_name', 'N/A')}")
    print(f"  Market: {bet.get('market', 'N/A')} {bet.get('line', 'N/A')}")
    print(f"  Status: {bet.get('status', 'N/A')}")
    print(f"  Wager: ${bet.get('wager_amount', 'N/A')}")
    print(f"  Actual Result: {bet.get('actual_result', 'N/A')}")
    print(f"  Profit/Loss: ${bet.get('profit_loss', 'N/A')}")
    print(f"  Result Confirmed: {bet.get('result_confirmed', 'N/A')}")

# Check settings
print("\n2. CHECKING SETTINGS...")
settings = sheet.read_settings()
print(f"Settings found: {json.dumps(settings, indent=2)}")

# Check phase confidence
print("\n3. CHECKING PHASE CONFIDENCE...")
phases = sheet.read_phase_confidence()
for phase in phases:
    print(f"  {phase['phase']}: {phase['wins']}-{phase['losses']} "
          f"(Total: {phase['total_bets']}, Win Rate: {phase['win_rate']}%)")

# Direct check of sheet structure
print("\n4. CHECKING SHEET STRUCTURE...")
try:
    worksheet = sheet.spreadsheet.worksheet('bets_log')
    all_values = worksheet.get_all_values()
    print(f"Bets log has {len(all_values)} rows (including header)")
    if len(all_values) > 1:
        print(f"Headers: {all_values[0]}")
        print(f"First data row: {all_values[1] if len(all_values) > 1 else 'No data'}")
except Exception as e:
    print(f"Error reading sheet: {e}")