"""Read graded results from paper_slips sheet."""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sheets_integration import get_sheets_service, SPREADSHEET_ID

def read_graded_results():
    """Read and display graded results."""
    service = get_sheets_service()
    if not service:
        print("Failed to get sheets service")
        return
    
    try:
        # Read the sheet including result columns
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='paper_slips!A1:O6'  # First 6 rows including headers
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            print("No data found")
            return
            
        # Print header
        print("\nGraded Results:")
        print("-" * 80)
        print(f"{'Row':<4} {'Player':<20} {'Type':<10} {'Pick':<6} {'Result':<8} {'P/L':<8}")
        print("-" * 80)
        
        # Print data rows
        for i, row in enumerate(values[1:6], 1):  # Skip header, show first 5 data rows
            if len(row) >= 14:  # Ensure we have enough columns
                player = row[2][:19]  # Truncate long names
                market = row[3][:9]
                pick = row[5]
                result = row[12] if len(row) > 12 and row[12] else "Pending"
                pl = row[13] if len(row) > 13 and row[13] else "0"
                print(f"{i:<4} {player:<20} {market:<10} {pick:<6} {result:<8} {pl:<8}")
                
    except Exception as e:
        print(f"Error reading results: {e}")

if __name__ == "__main__":
    read_graded_results()
