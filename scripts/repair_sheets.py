"""Repair Google Sheets data integrity issues for PhaseGrid."""
import os
from pathlib import Path
from googleapiclient.discovery import build
from google.oauth2 import service_account
import time
from typing import List, Dict, Any
from modules.sheet_connector import BetSyncSheetConnector

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = os.getenv('SHEET_ID', '1-VX73...VZM')
DEFAULT_BANKROLL = 10000

class SheetRepair:
    def __init__(self):
        creds_path = Path(os.getenv('GOOGLE_CREDS', 'credentials.json'))
        if not creds_path.exists():
            raise FileNotFoundError(
                f"Google credentials not found at {creds_path}. "
                "Please ensure credentials.json exists or set GOOGLE_CREDS env var."
            )
        try:
            creds = service_account.Credentials.from_service_account_file(
                str(creds_path), scopes=SCOPES)
            self.service = build('sheets', 'v4', credentials=creds)
            self.sheet = self.service.spreadsheets()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Google Sheets service: {e}")
        
    def get_sheet_data(self, range_name: str) -> List[List[Any]]:
        """Fetch data from a sheet range."""
        try:
            result = self.sheet.values().get(
                spreadsheetId=SHEET_ID, range=range_name).execute()
            return result.get('values', [])
        except Exception as e:
            print(f"Error fetching {range_name}: {e}")
            return []
    
    def remove_duplicate_headers(self, tab_name: str) -> int:
        """Remove duplicate header rows from a tab."""
        data = self.get_sheet_data(f"{tab_name}!A:Z")
        if not data or len(data) < 2:
            return 0
            
        header = data[0]
        duplicates_removed = 0
        rows_to_delete = []
        
        # Find duplicate header rows
        for i, row in enumerate(data[1:], start=2):
            if row == header:
                rows_to_delete.append(i)
                duplicates_removed += 1
        
        # Delete rows in reverse order
        for row_idx in reversed(rows_to_delete):
            try:
                request = {
                    'deleteDimension': {
                        'range': {
                            'sheetId': self._get_sheet_id(tab_name),
                            'dimension': 'ROWS',
                            'startIndex': row_idx - 1,
                            'endIndex': row_idx
                        }
                    }
                }
                self.sheet.batchUpdate(
                    spreadsheetId=SHEET_ID,
                    body={'requests': [request]}).execute()
                time.sleep(1)  # Rate limit protection
            except Exception as e:
                print(f"Error deleting row {row_idx} in {tab_name}: {e}")
                
        return duplicates_removed
    
    def fix_column_names(self, tab_name: str) -> bool:
        """Ensure column names match spec (bet_id -> source_id)."""
        data = self.get_sheet_data(f"{tab_name}!A1:Z1")
        if not data or not data[0]:
            return False
            
        header = data[0]
        updated = False
        
        # Replace bet_id with source_id
        for i, col in enumerate(header):
            if col.lower() == 'bet_id':
                header[i] = 'source_id'
                updated = True
        
        if updated:
            try:
                self.sheet.values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"{tab_name}!A1:Z1",
                    valueInputOption='RAW',
                    body={'values': [header]}).execute()
                time.sleep(1)
                return True
            except Exception as e:
                print(f"Error updating headers in {tab_name}: {e}")
                
        return False
    
    def ensure_bankroll_setting(self) -> bool:
        """Ensure Bankroll row exists in settings tab."""
        settings_data = self.get_sheet_data("settings!A:B")
        
        # Check if Bankroll exists
        has_bankroll = any(
            row[0].lower() == 'bankroll' 
            for row in settings_data if row and len(row) > 0
        )
        
        if not has_bankroll:
            bankroll_value = os.getenv('BANKROLL', str(DEFAULT_BANKROLL))
            try:
                self.sheet.values().append(
                    spreadsheetId=SHEET_ID,
                    range="settings!A:B",
                    valueInputOption='RAW',
                    body={'values': [['Bankroll', bankroll_value]]}).execute()
                time.sleep(1)
                return True
            except Exception as e:
                print(f"Error adding Bankroll setting: {e}")
                return False
                
        return True
    
    def _get_sheet_id(self, tab_name: str) -> int:
        """Get sheet ID for a tab name."""
        try:
            sheet_metadata = self.sheet.get(spreadsheetId=SHEET_ID).execute()
            for sheet in sheet_metadata.get('sheets', []):
                if sheet['properties']['title'] == tab_name:
                    return sheet['properties']['sheetId']
        except Exception as e:
            print(f"Error getting sheet ID for {tab_name}: {e}")
        return 0
    
    def repair_all(self) -> Dict[str, Any]:
        """Run all repair operations."""
        results = {
            'duplicates_removed': {},
            'columns_fixed': [],
            'bankroll_added': False
        }
        
        # Fix duplicate headers in critical tabs
        for tab in ['slips_log', 'bets_log', 'results_log']:
            removed = self.remove_duplicate_headers(tab)
            if removed > 0:
                results['duplicates_removed'][tab] = removed
        
        # Fix column names
        for tab in ['slips_log', 'bets_log', 'results_log']:
            if self.fix_column_names(tab):
                results['columns_fixed'].append(tab)
        
        # Ensure bankroll setting
        results['bankroll_added'] = self.ensure_bankroll_setting()
        
        return results


def main():
    """Execute sheet repairs."""
    try:
        print("Starting Google Sheets repair...")
        repair = SheetRepair()
        results = repair.repair_all()
        
        print("\nRepair Summary:")
        print(f"• Duplicates removed: {results['duplicates_removed']}")
        print(f"• Columns fixed: {results['columns_fixed']}")
        print(f"• Bankroll added: {results['bankroll_added']}")
        
        return results
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        print("Please ensure you have credentials.json in the project directory.")
        return None
    except Exception as e:
        print(f"\nERROR: Failed to repair sheets: {e}")
        return None


if __name__ == "__main__":
    main()