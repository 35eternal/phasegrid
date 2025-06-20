from modules.sheet_connector import SheetConnector
import pandas as pd
import json
from datetime import datetime

# Test what columns the sheet connector expects
sc = SheetConnector()
sc.connect()

# Create a test DataFrame with the exact columns from bets_log
test_data = {
    'source_id': 'TEST_SLIP_001',
    'timestamp': datetime.now().isoformat(),
    'player_name': 'TEST POWER 3-pick',
    'market': 'parlay',
    'line': 3,
    'phase': 'follicular',
    'adjusted_prediction': 0.05,
    'wager_amount': 10.0,
    'odds': 10.0,
    'status': 'pending',
    'actual_result': '',
    'result_confirmed': False,
    'profit_loss': 0.0,
    'notes': json.dumps([{'prop_id': 'P001'}])
}

test_df = pd.DataFrame([test_data])
print("Test DataFrame columns:")
print(list(test_df.columns))
print("\nTrying to push test slip...")

try:
    success = sc.push_slips(test_df)
    print(f"Push result: {success}")
except Exception as e:
    print(f"Push failed: {e}")
    import traceback
    traceback.print_exc()
