from modules.sheet_connector import BetSyncSheetConnector

print("=== FIXING EMPTY ROWS IN GOOGLE SHEET ===")

sheet = BetSyncSheetConnector()

try:
    worksheet = sheet.spreadsheet.worksheet('bets_log')
    
    # Get all values
    all_values = worksheet.get_all_values()
    print(f"Current sheet has {len(all_values)} rows")
    
    # Find non-empty rows
    non_empty_rows = []
    for i, row in enumerate(all_values):
        # Check if row has any non-empty cells
        if any(cell.strip() for cell in row):
            non_empty_rows.append(row)
    
    print(f"Found {len(non_empty_rows)} non-empty rows")
    
    # Show what we found
    print("\nNon-empty rows:")
    for i, row in enumerate(non_empty_rows[:5]):  # Show first 5
        if i == 0:
            print(f"Headers: {row[:4]}...")  # Show first 4 columns
        else:
            print(f"Row {i}: {row[2]} - {row[3]} {row[4]} - Status: {row[9]}")
    
    print("\nTo fix this:")
    print("1. Open your Google Sheet")
    print("2. Select all empty rows (2-1000)")
    print("3. Right-click → Delete rows")
    print("4. Your bets will be visible at the top!")
    
except Exception as e:
    print(f"Error: {e}")