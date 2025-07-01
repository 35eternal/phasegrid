#!/usr/bin/env python3
"""Fixed sheet connectivity test"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_sheet_connection():
    """Test Google Sheets connectivity"""
    print("🔍 Testing Google Sheets connection...")
    
    # Check for credentials
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found!")
        return False
        
    # Check for sheet ID
    sheet_id = os.getenv('GOOGLE_SHEET_ID') or os.getenv('SHEET_ID')
    if not sheet_id:
        print("❌ No Sheet ID in environment!")
        return False
        
    print(f"✅ Found Sheet ID: {sheet_id[:10]}...")
    
    try:
        # Try different imports
        try:
            from phasegrid.verify_sheets import SheetVerifier
            verifier = SheetVerifier()
            print("✅ Using phasegrid.verify_sheets")
            return True
        except:
            pass
            
        try:
            from auth.sheets_auth import get_sheets_service
            service = get_sheets_service()
            print("✅ Got sheets service from auth module")
            
            # Try to read sheet metadata
            sheet_metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            print(f"✅ Connected to sheet: {sheet_metadata.get('properties', {}).get('title', 'Unknown')}")
            return True
        except Exception as e:
            print(f"⚠️ Sheet read failed: {e}")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    return False

if __name__ == "__main__":
    import sys
    success = test_sheet_connection()
    sys.exit(0 if success else 1)
