from modules.sheet_connector import BetSyncSheetConnector
from datetime import datetime, timedelta

sheet = BetSyncSheetConnector()

# Get last 30 days of bets
history = sheet.get_bet_history(days_back=30)

# Calculate metrics
total_bets = len(history)
wins = sum(1 for bet in history if bet.get('status') == 'won')
losses = sum(1 for bet in history if bet.get('status') == 'lost')
pending = sum(1 for bet in history if bet.get('status') == 'pending')

# Helper function to safely convert to float
def safe_float(value, default=0):
    """Convert value to float, handling empty strings and None"""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

total_wagered = sum(safe_float(bet.get('wager_amount', 0)) for bet in history)
total_profit = sum(safe_float(bet.get('profit_loss', 0)) for bet in history)

print(f"\n=== 30-DAY PERFORMANCE ===")
print(f"Total Bets: {total_bets}")
print(f"Record: {wins}-{losses} ({pending} pending)")
if wins + losses > 0:
    win_rate = wins / (wins + losses) * 100
    print(f"Win Rate: {win_rate:.1f}%")
print(f"Total Wagered: ${total_wagered:.2f}")
print(f"Net Profit: ${total_profit:.2f}")
print(f"ROI: {(total_profit/total_wagered*100):.1f}%" if total_wagered > 0 else "ROI: N/A")

# Performance by phase
print(f"\n=== PHASE PERFORMANCE ===")
phases = sheet.read_phase_confidence()
for phase in phases:
    print(f"{phase['phase']}: {phase['win_rate']}% ({phase['wins']}-{phase['losses']})")

# Recent bets detail
print(f"\n=== RECENT BETS (Last 5) ===")
for bet in history[-5:]:  # Last 5 bets
    status = bet.get('status', 'pending')
    pl = safe_float(bet.get('profit_loss', 0))
    pl_display = f"${pl:+.2f}" if status != 'pending' else "pending"
    print(f"{bet.get('timestamp', '')[:10]} - {bet.get('player_name', 'Unknown')} "
          f"{bet.get('market', '')} {bet.get('line', '')} "
          f"[{status.upper()}] {pl_display}")