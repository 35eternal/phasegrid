#!/usr/bin/env python3
"""Wrapper for generating 1-day dry-run slips and pushing to Google Sheet."""

from slips_generator import generate_slips
import os
import uuid
import datetime
import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build


def main():
    """Generate dry-run slips for today and push to Google Sheets."""
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    # Batch parameters
    today = datetime.date.today().isoformat()
    logger.info(f"Generating slips for date: {today}")
    
    try:
        slips = generate_slips(start_date=today, end_date=today)
        batch_id = str(uuid.uuid4())
        logger.info(f"Generated {len(slips)} slips with batch_id: {batch_id}")
        
        # Mark as dry-run
        for slip in slips:
            slip['batch_id'] = batch_id
            slip['dry_run'] = True
        
        # Google Sheets auth
        sheet_id = os.environ.get('SHEET_ID')
        google_sa_json = os.environ.get('GOOGLE_SA_JSON')
        
        if not sheet_id or not google_sa_json:
            raise ValueError("Missing SHEET_ID or GOOGLE_SA_JSON environment variables")
        
        # Parse credentials
        if os.path.exists(google_sa_json):
            # It's a file path
            credentials = service_account.Credentials.from_service_account_file(
                google_sa_json,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
        else:
            # It's a JSON string
            service_account_info = json.loads(google_sa_json)
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
        
        # Build service
        service = build('sheets', 'v4', credentials=credentials)
        
        # Convert slips to rows
        # Assuming sheet columns are the keys of the slip dict
        if slips:
            headers = list(slips[0].keys())
            rows = [headers]  # Include headers
            for slip in slips:
                row = [slip.get(header, '') for header in headers]
                rows.append(row)
        else:
            logger.warning("No slips generated")
            return
        
        # Push to sheet
        range_name = 'paper_slips!A1'  # Worksheet named "paper_slips"
        body = {
            'values': rows[1:]  # Skip headers if sheet already has them
        }
        
        result = service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        logger.info(f"Pushed {len(slips)} dry-run slips with batch_id={batch_id}")
        logger.info(f"Sheet updated: {result.get('updates', {}).get('updatedCells', 0)} cells")
        
    except Exception as e:
        logger.error(f"Error in auto_paper: {str(e)}")
        raise


if __name__ == "__main__":
    main()
