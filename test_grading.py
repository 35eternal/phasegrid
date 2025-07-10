"""Test grading functionality."""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sheets_integration import get_sheets_service, SPREADSHEET_ID

def simulate_grading():
    """Simulate grading by updating some results."""
    service = get_sheets_service()
    if not service:
        print("Failed to get sheets service")
        return
    
    try:
        # Read current data
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='paper_slips!A2:O20'
        ).execute()
        
        values = result.get('values', [])
        print(f"Found {len(values)} bets to grade")
        
        # Simulate some results (Win/Loss)
        # In real grading, this would come from actual game results
        updates = []
        for i, row in enumerate(values[:5]):  # Grade first 5 bets
            row_num = i + 2  # Account for header row
            result = "Win" if i % 2 == 0 else "Loss"
            profit_loss = 9.09 if result == "Win" else -10.0  # Based on -110 odds
            
            updates.append({
                'range': f'paper_slips!M{row_num}:N{row_num}',
                'values': [[result, profit_loss]]
            })
        
        if updates:
            body = {
                'valueInputOption': 'USER_ENTERED',
                'data': updates
            }
            
            result = service.spreadsheets().values().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=body
            ).execute()
            
            print(f"Updated {len(updates)} bets with simulated results")
            
    except Exception as e:
        print(f"Error simulating grading: {e}")

if __name__ == "__main__":
    simulate_grading()
