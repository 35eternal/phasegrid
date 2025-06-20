"""Verify Google Sheets structure and data integrity."""
import os
from pathlib import Path
from googleapiclient.discovery import build
from google.oauth2 import service_account
from typing import Dict, List, Any
from modules.sheet_connector import BetSyncSheetConnector

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = os.getenv('SHEET_ID', '1-VX73...VZM')


class SheetVerifier:
    """Verify sheet structure and data integrity."""
    
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
            self.connector = BetSyncSheetConnector(self.service, sheet_id=SHEET_ID)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Google Sheets service: {e}")
    
    def verify_tabs_exist(self) -> Dict[str, bool]:
        """Verify required tabs exist."""
        required_tabs = ['slips_log', 'bets_log', 'results_log', 'settings']
        results = {}
        
        try:
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=SHEET_ID).execute()
            existing_tabs = [
                sheet['properties']['title'] 
                for sheet in sheet_metadata.get('sheets', [])
            ]
            
            for tab in required_tabs:
                results[tab] = tab in existing_tabs
                
        except Exception as e:
            print(f"Error checking tabs: {e}")
            for tab in required_tabs:
                results[tab] = False
                
        return results
    
    def verify_headers(self, tab_name: str, expected_headers: List[str]) -> Dict[str, Any]:
        """Verify headers match expected format."""
        try:
            data = self.connector.get_data(f"{tab_name}!A1:Z1")
            if not data or not data[0]:
                return {"valid": False, "error": "No headers found"}
            
            actual_headers = data[0]
            missing = set(expected_headers) - set(actual_headers)
            extra = set(actual_headers) - set(expected_headers)
            
            # Check for bet_id (should be source_id)
            has_bet_id = 'bet_id' in actual_headers
            
            return {
                "valid": len(missing) == 0 and not has_bet_id,
                "missing": list(missing),
                "extra": list(extra),
                "has_bet_id": has_bet_id,
                "actual": actual_headers
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def verify_bankroll_setting(self) -> Dict[str, Any]:
        """Verify bankroll setting exists."""
        try:
            data = self.connector.get_data("settings!A:B")
            
            for row in data:
                if row and len(row) >= 2 and row[0].lower() == 'bankroll':
                    try:
                        value = float(row[1])
                        return {"exists": True, "value": value}
                    except ValueError:
                        return {"exists": True, "value": None, "error": "Invalid value"}
            
            return {"exists": False}
            
        except Exception as e:
            return {"exists": False, "error": str(e)}
    
    def run_verification(self) -> Dict[str, Any]:
        """Run all verification checks."""
        print("Running Google Sheets verification...")
        
        results = {
            "tabs": self.verify_tabs_exist(),
            "headers": {},
            "bankroll": self.verify_bankroll_setting()
        }
        
        # Expected headers for each tab
        expected_headers = {
            "slips_log": ["source_id", "timestamp", "amount", "odds", "status"],
            "bets_log": ["source_id", "timestamp", "stake", "odds", "phase"],
            "results_log": ["source_id", "result", "pnl", "timestamp"]
        }
        
        for tab, headers in expected_headers.items():
            if results["tabs"].get(tab, False):
                results["headers"][tab] = self.verify_headers(tab, headers)
        
        return results


def main():
    """Execute sheet verification."""
    try:
        verifier = SheetVerifier()
        results = verifier.run_verification()
        
        print("\n=== Sheet Verification Results ===")
        
        # Tab existence
        print("\nTab Status:")
        for tab, exists in results["tabs"].items():
            status = "✓" if exists else "✗"
            print(f"  {status} {tab}")
        
        # Header validation
        print("\nHeader Status:")
        for tab, header_info in results["headers"].items():
            if header_info.get("valid"):
                print(f"  ✓ {tab} - Headers valid")
            else:
                print(f"  ✗ {tab} - Issues found:")
                if header_info.get("missing"):
                    print(f"    - Missing: {header_info['missing']}")
                if header_info.get("has_bet_id"):
                    print(f"    - Found 'bet_id' (should be 'source_id')")
                if header_info.get("error"):
                    print(f"    - Error: {header_info['error']}")
        
        # Bankroll setting
        print("\nBankroll Setting:")
        if results["bankroll"].get("exists"):
            value = results["bankroll"].get("value", "Unknown")
            print(f"  ✓ Exists: ${value}")
        else:
            print(f"  ✗ Missing")
            if results["bankroll"].get("error"):
                print(f"    - Error: {results['bankroll']['error']}")
        
        return results
        
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        return None
    except Exception as e:
        print(f"\nERROR: Failed to verify sheets: {e}")
        return None


if __name__ == "__main__":
    main()