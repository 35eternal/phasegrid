from modules.sheet_connector import SheetConnector
import pandas as pd

def main():
    """Check columns in the sheet."""
    try:
        sc = SheetConnector()
        # SheetConnector might not have connect method, try direct access
        if hasattr(sc, 'connect'):
            sc.connect()
        
        # Try to get worksheet
        if hasattr(sc, 'spreadsheet'):
            worksheet = sc.spreadsheet.worksheet('slips_log')
            headers = worksheet.row_values(1)
            
            print("Columns in slips_log worksheet:")
            for i, header in enumerate(headers):
                print(f"  {i+1}. {header}")
        else:
            print("SheetConnector doesn't have spreadsheet attribute")
            print("Available attributes:", dir(sc))
            
    except Exception as e:
        print(f"Error accessing sheet: {e}")
        print("Using mock data for testing")
        
        # Mock headers for testing
        headers = ['Date', 'Bet ID', 'Player', 'Market', 'Line', 'Stake', 'Odds', 'Payout', 'Result']
        print("Mock columns in slips_log worksheet:")
        for i, header in enumerate(headers):
            print(f"  {i+1}. {header}")

if __name__ == "__main__":
    main()