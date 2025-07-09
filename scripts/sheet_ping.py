from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
#!/usr/bin/env python3
"""
Sheet Ping - Quick health check for Google Sheets connection
Exit codes:
  0 - Success
  1 - Connection failed
  2 - Authentication failed
  3 - Sheet not accessible
"""
import os
import sys
import json
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.sheets_auth import get_sheets_service

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def ping_sheet():
    """Test Google Sheets connection and access"""
    try:
        # Check for required environment variables
        sheet_id = os.getenv('SHEET_ID') or os.getenv('GOOGLE_SHEET_ID')
        if not sheet_id:
            logger.error("âŒ SHEET_ID environment variable not set")
            return 2
        
        if not os.getenv('GOOGLE_SA_JSON'):
            logger.error("âŒ GOOGLE_SA_JSON environment variable not set")
            return 2
        
        logger.info(f"ðŸ” Attempting to ping sheet: {sheet_id}")
        
        # Get sheets service
        try:
            service = get_sheets_service()
            logger.info("âœ… Google Sheets authentication successful")
        except Exception as auth_error:
            logger.error(f"âŒ Authentication failed: {auth_error}")
            return 2
        
        # Try to read sheet metadata
        try:
            sheet_metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            sheet_title = sheet_metadata.get('properties', {}).get('title', 'Unknown')
            logger.info(f"âœ… Successfully connected to sheet: '{sheet_title}'")
            
            # Try to read a cell to ensure read access
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range='A1'
            ).execute()
            
            logger.info("âœ… Sheet read access confirmed")
            
            # Log success details
            logger.info(f"ðŸ“Š Sheet ping successful at {datetime.now().isoformat()}")
            return 0
            
        except Exception as sheet_error:
            logger.error(f"âŒ Cannot access sheet: {sheet_error}")
            return 3
            
    except Exception as e:
        logger.error(f"âŒ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = ping_sheet()
    
    if exit_code == 0:
        print("\nâœ… Sheet ping successful! Google Sheets connection is healthy.")
    else:
        print(f"\nâŒ Sheet ping failed with exit code {exit_code}")
    
    sys.exit(exit_code)
