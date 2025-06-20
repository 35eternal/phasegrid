import sys
sys.path.append('.')
from modules.sheet_connector import SheetConnector

sheet_id = "1-VX73LvsxtpO4D15dsaYso3UjGzYcmsFJUx0io6_VZM"
connector = SheetConnector(sheet_id=sheet_id)

# Add bankroll to settings
ws = connector.spreadsheet.worksheet('settings')
all_values = ws.get_all_values()

# Check if bankroll exists
bankroll_exists = any('bankroll' in str(row).lower() for row in all_values)

if not bankroll_exists:
    # Find next empty row
    next_row = len(all_values) + 1
    # Add bankroll setting
    ws.update(f'A{next_row}:B{next_row}', [['Bankroll', '1000']])
    print("Added Bankroll setting with default value 1000")
else:
    print("Bankroll setting already exists")
