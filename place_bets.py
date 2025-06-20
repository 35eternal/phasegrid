#!/usr/bin/env python3
from modules.sheet_connector import BetSyncSheetConnector
from datetime import datetime

# Initialize connection
sheet = BetSyncSheetConnector()

# Example: Place a new bet
new_bet = {
    'source_id': f'WNBA_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
    'timestamp': datetime.now().isoformat(),
    'player_name': 'Breanna Stewart',
    'market': 'points_over',
    'line': 21.5,
    'phase': 'high_confidence',
    'adjusted_prediction': 24.3,
    'wager_amount': 50,
    'odds': 1.91,
    'notes': 'Strong matchup vs interior defense'
}

# Write to sheet
written, skipped = sheet.write_new_bets([new_bet])
print(f"Successfully placed {written} bets")