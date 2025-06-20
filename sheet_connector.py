"""Enhanced Google Sheets connector with adaptive throttling."""
import time
from typing import List, Dict, Any, Optional
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)

class AdaptiveThrottle:
    """Implements exponential backoff for rate limiting."""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 16.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.current_delay = base_delay
        self.consecutive_errors = 0
        
    def wait(self):
        """Wait with current delay."""
        time.sleep(self.current_delay)
        
    def on_success(self):
        """Reset delay on successful request."""
        self.current_delay = self.base_delay
        self.consecutive_errors = 0
        
    def on_error(self, error_code: int):
        """Increase delay on error (429 or 503)."""
        if error_code in [429, 503]:
            self.consecutive_errors += 1
            self.current_delay = min(
                self.base_delay * (2 ** self.consecutive_errors),
                self.max_delay
            )
            logger.info(f"Rate limited. Backing off for {self.current_delay}s")
            time.sleep(self.current_delay)


class SheetConnector:
    """Google Sheets connector with adaptive rate limiting."""
    
    def __init__(self, service, sheet_id: str):
        self.service = service
        self.sheet_id = sheet_id
        self.throttle = AdaptiveThrottle()
        self.batch_size = 50  # Start conservative
        
    def push_batch(self, tab_name: str, data: List[List[Any]], 
                   start_row: int = 2) -> bool:
        """Push data in batches with adaptive throttling."""
        if not data:
            return True
            
        total_rows = len(data)
        pushed_rows = 0
        
        while pushed_rows < total_rows:
            batch = data[pushed_rows:pushed_rows + self.batch_size]
            range_name = f"{tab_name}!A{start_row + pushed_rows}:Z{start_row + pushed_rows + len(batch) - 1}"
            
            try:
                self.throttle.wait()
                
                result = self.service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body={'values': batch}
                ).execute()
                
                self.throttle.on_success()
                pushed_rows += len(batch)
                
                # Adaptive batch sizing
                if self.batch_size < 100:
                    self.batch_size = min(self.batch_size + 10, 100)
                    
                logger.info(f"Pushed {pushed_rows}/{total_rows} rows to {tab_name}")
                
            except HttpError as e:
                if e.resp.status in [429, 503]:
                    self.throttle.on_error(e.resp.status)
                    # Reduce batch size on rate limit
                    self.batch_size = max(10, self.batch_size // 2)
                    logger.warning(f"Reduced batch size to {self.batch_size}")
                else:
                    logger.error(f"HTTP error: {e}")
                    return False
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return False
                
        return True
    
    def get_data(self, range_name: str) -> List[List[Any]]:
        """Fetch data with retry logic."""
        attempts = 0
        while attempts < 3:
            try:
                self.throttle.wait()
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=self.sheet_id,
                    range=range_name
                ).execute()
                self.throttle.on_success()
                return result.get('values', [])
            except HttpError as e:
                if e.resp.status in [429, 503]:
                    self.throttle.on_error(e.resp.status)
                    attempts += 1
                else:
                    raise
            except Exception as e:
                logger.error(f"Error fetching data: {e}")
                return []
        
        return []
    
    def append_row(self, tab_name: str, row_data: List[Any]) -> bool:
        """Append a single row with source_id column support."""
        # Ensure source_id is used (not bet_id)
        if isinstance(row_data, dict):
            if 'bet_id' in row_data:
                row_data['source_id'] = row_data.pop('bet_id')
                
        try:
            self.throttle.wait()
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=f"{tab_name}!A:Z",
                valueInputOption='RAW',
                body={'values': [row_data]}
            ).execute()
            self.throttle.on_success()
            return True
        except HttpError as e:
            if e.resp.status in [429, 503]:
                self.throttle.on_error(e.resp.status)
                # Retry once after backoff
                return self.append_row(tab_name, row_data)
            else:
                logger.error(f"Error appending row: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error appending row: {e}")
            return False
    
    def clear_range(self, range_name: str) -> bool:
        """Clear a range with retry logic."""
        try:
            self.throttle.wait()
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.sheet_id,
                range=range_name
            ).execute()
            self.throttle.on_success()
            return True
        except HttpError as e:
            if e.resp.status in [429, 503]:
                self.throttle.on_error(e.resp.status)
                return self.clear_range(range_name)
            else:
                logger.error(f"Error clearing range: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error clearing range: {e}")
            return False


def normalize_column_mapping(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all bet_id references are converted to source_id."""
    if 'bet_id' in data:
        data['source_id'] = data.pop('bet_id')
    
    # Handle nested structures
    for key, value in data.items():
        if isinstance(value, dict):
            data[key] = normalize_column_mapping(value)
        elif isinstance(value, list):
            data[key] = [
                normalize_column_mapping(item) if isinstance(item, dict) else item
                for item in value
            ]
    
    return data