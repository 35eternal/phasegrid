from modules.sheet_connector import SheetConnector
import pandas as pd

sc = SheetConnector()
sc.connect()

# Get the headers from slips_log
worksheet = sc.spreadsheet.worksheet('slips_log')
headers = worksheet.row_values(1)

print("Columns in slips_log worksheet:")
for i, header in enumerate(headers):
    print(f"  {i+1}. {header}")

# Also check what the push_slips method validation expects
print("\nChecking push_slips method...")
