import sys
sys.path.append('.')
from modules.sheet_connector import SheetConnector

sheet_id = "1-VX73LvsxtpO4D15dsaYso3UjGzYcmsFJUx0io6_VZM"
connector = SheetConnector(sheet_id=sheet_id)

# Check bets_log headers
ws = connector.spreadsheet.worksheet('bets_log')
current_headers = ws.get_all_values()[0] if ws.get_all_values() else []
print(f"Current bets_log headers: {current_headers}")

# Expected headers (from verify_sheets.py)
expected = ['bet_id', 'date', 'player', 'stat', 'line', 'over_under', 'confidence', 
            'odds', 'result', 'win_loss', 'payout', 'phase']
print(f"Expected headers: {expected}")

# Fix if they contain source_id instead of bet_id
if 'source_id' in current_headers and 'bet_id' not in current_headers:
    fixed_headers = [h.replace('source_id', 'bet_id') for h in current_headers]
    ws.update('A1:' + chr(65 + len(fixed_headers) - 1) + '1', [fixed_headers])
    print(f"Fixed bets_log headers: {fixed_headers}")
