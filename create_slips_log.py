from modules.sheet_connector import SheetConnector

sc = SheetConnector()
sc.connect()

# Check if slips_log exists, if not create it
try:
    worksheet = sc.spreadsheet.worksheet('slips_log')
    print("slips_log worksheet already exists")
except:
    print("Creating slips_log worksheet...")
    
    # Create new worksheet
    worksheet = sc.spreadsheet.add_worksheet(title='slips_log', rows=1000, cols=20)
    
    # Add headers
    headers = [
        'slip_id', 'created', 'timestamp', 'ticket_type', 'props', 
        'n_props', 'ev', 'stake', 'odds', 'status', 'payout', 'settled_at'
    ]
    worksheet.append_row(headers)
    
    print("✅ Created slips_log worksheet with headers")
    
# List all worksheets
print("\nAvailable worksheets:")
for ws in sc.spreadsheet.worksheets():
    print(f"  - {ws.title}")
