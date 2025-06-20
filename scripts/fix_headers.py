import sys
sys.path.append('.')
from modules.sheet_connector import SheetConnector

def fix_duplicate_headers():
    # Use the sheet_id directly
    sheet_id = "1-VX73LvsxtpO4D15dsaYso3UjGzYcmsFJUx0io6_VZM"
    
    connector = SheetConnector(sheet_id=sheet_id)
    
    # Get the worksheet - connector auto-connects
    ws = connector.spreadsheet.worksheet('slips_log')
    
    # Get all values
    all_values = ws.get_all_values()
    
    if len(all_values) > 0:
        # Get unique headers
        headers = all_values[0]
        print(f"Current headers: {headers}")
        
        unique_headers = []
        seen = set()
        
        for h in headers:
            if h in seen:
                # Add number suffix for duplicates
                i = 2
                while f"{h}_{i}" in seen:
                    i += 1
                unique_headers.append(f"{h}_{i}")
                seen.add(f"{h}_{i}")
            else:
                unique_headers.append(h)
                seen.add(h)
        
        # Update first row with unique headers
        ws.update('A1:' + chr(65 + len(headers) - 1) + '1', [unique_headers])
        print(f"Fixed headers: {unique_headers}")
        print(f"Total columns: {len(unique_headers)}")

if __name__ == "__main__":
    fix_duplicate_headers()
