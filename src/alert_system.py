"""
AlertSystem - Enhanced with exponential backoff retry logic and error handling
"""

import os
import json
import time
import logging
import requests
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Types of alerts that can be sent."""
    HIGH_ROI = "high_roi"
    LOW_ROI = "low_roi"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SYSTEM_FAILURE = "system_failure"


class RetryConfig:
    """Configuration for retry logic."""
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay


def exponential_backoff_retry(retry_config: RetryConfig):
    """Decorator for exponential backoff retry logic."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(retry_config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < retry_config.max_attempts - 1:
                        # Calculate delay with exponential backoff
                        delay = min(
                            retry_config.base_delay * (2 ** attempt),
                            retry_config.max_delay
                        )
                        logger.warning(
                            f"Attempt {attempt + 1}/{retry_config.max_attempts} failed: {e}. "
                            f"Retrying in {delay:.1f} seconds..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"All {retry_config.max_attempts} attempts failed.")
            
            raise last_exception
        return wrapper
    return decorator


class AlertSystem:
    """System for sending alerts via Discord, Slack, and other channels."""
    
    def __init__(self):
        # Load webhook URLs from environment
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        
        # ROI thresholds from environment
        self.high_roi_threshold = float(os.getenv('HIGH_ROI_THRESHOLD', '0.20'))
        self.low_roi_threshold = float(os.getenv('LOW_ROI_THRESHOLD', '-0.20'))
        
        # Retry configuration
        self.retry_config = RetryConfig(
            max_attempts=int(os.getenv('ALERT_MAX_RETRIES', '3')),
            base_delay=float(os.getenv('ALERT_BASE_DELAY', '1.0')),
            max_delay=float(os.getenv('ALERT_MAX_DELAY', '60.0'))
        )
        
        # Validate webhooks on initialization
        self._validate_webhooks()
        
        logger.info("AlertSystem initialized")
    
    def _validate_webhooks(self):
        """Validate webhook configurations."""
        if not self.discord_webhook and not self.slack_webhook:
            logger.warning("No webhook URLs configured. Alerts will only be logged.")
        else:
            if self.discord_webhook:
                logger.info("Discord webhook configured")
            if self.slack_webhook:
                logger.info("Slack webhook configured")
    
    def send_alert(self, alert_type: AlertType, message: str, data: Optional[Dict[str, Any]] = None):
        """Send an alert through configured channels."""
        alert_data = {
            'type': alert_type.value,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'data': data or {}
        }
        
        # Log the alert
        self._log_alert(alert_data)
        
        # Send to Discord
        if self.discord_webhook:
            try:
                self._send_to_discord(alert_data)
            except Exception as e:
                logger.error(f"Failed to send Discord alert: {e}")
        
        # Send to Slack
        if self.slack_webhook:
            try:
                self._send_to_slack(alert_data)
            except Exception as e:
                logger.error(f"Failed to send Slack alert: {e}")
        
        # If no webhooks configured, ensure it's logged
        if not self.discord_webhook and not self.slack_webhook:
            logger.warning(f"Alert not sent to external channels: {message}")
    
    def _log_alert(self, alert_data: Dict[str, Any]):
        """Log alert locally."""
        if alert_data['type'] in ['error', 'system_failure']:
            logger.error(f"ALERT: {alert_data['message']}")
        elif alert_data['type'] == 'warning':
            logger.warning(f"ALERT: {alert_data['message']}")
        else:
            logger.info(f"ALERT: {alert_data['message']}")
    
    @exponential_backoff_retry(RetryConfig())
    def _send_to_webhook(self, url: str, payload: Dict[str, Any], timeout: int = 10):
        """Generic webhook sender with retry logic."""
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        return response
    
    def _send_to_discord(self, alert_data: Dict[str, Any]):
        """Send alert to Discord."""
        # Format for Discord
        color = self._get_discord_color(alert_data['type'])
        
        embed = {
            "title": f"PhaseGrid Alert: {alert_data['type'].upper()}",
            "description": alert_data['message'],
            "color": color,
            "timestamp": alert_data['timestamp'],
            "fields": []
        }
        
        # Add data fields
        if alert_data['data']:
            for key, value in alert_data['data'].items():
                if key != 'trades_detail':  # Skip large data
                    embed['fields'].append({
                        "name": key.replace('_', ' ').title(),
                        "value": str(value)[:1024],  # Discord field limit
                        "inline": True
                    })
        
        payload = {"embeds": [embed]}
        
        try:
            self._send_to_webhook(self.discord_webhook, payload)
            logger.debug("Discord alert sent successfully")
        except Exception as e:
            logger.error(f"Discord webhook failed after retries: {e}")
            raise
    
    def _send_to_slack(self, alert_data: Dict[str, Any]):
        """Send alert to Slack."""
        # Format for Slack
        icon = self._get_slack_icon(alert_data['type'])
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{icon} PhaseGrid {alert_data['type'].upper()} Alert"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": alert_data['message']
                }
            }
        ]
        
        # Add data as fields
        if alert_data['data']:
            fields = []
            for key, value in alert_data['data'].items():
                if key != 'trades_detail':  # Skip large data
                    fields.append({
                        "type": "mrkdwn",
                        "text": f"*{key.replace('_', ' ').title()}:*\n{value}"
                    })
            
            if fields:
                blocks.append({
                    "type": "section",
                    "fields": fields[:10]  # Slack limit
                })
        
        # Add timestamp
        blocks.append({
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": f"_Generated at {alert_data['timestamp']}_"
            }]
        })
        
        payload = {"blocks": blocks}
        
        try:
            self._send_to_webhook(self.slack_webhook, payload)
            logger.debug("Slack alert sent successfully")
        except Exception as e:
            logger.error(f"Slack webhook failed after retries: {e}")
            raise
    
    def _get_discord_color(self, alert_type: str) -> int:
        """Get Discord embed color based on alert type."""
        colors = {
            'high_roi': 0x00FF00,  # Green
            'low_roi': 0xFF0000,   # Red
            'error': 0xFF0000,     # Red
            'warning': 0xFFFF00,   # Yellow
            'info': 0x0000FF,      # Blue
            'system_failure': 0x800080  # Purple
        }
        return colors.get(alert_type, 0x808080)  # Default gray
    
    def _get_slack_icon(self, alert_type: str) -> str:
        """Get Slack icon based on alert type."""
        icons = {
            'high_roi': '📈',
            'low_roi': '📉',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'system_failure': '🚨'
        }
        return icons.get(alert_type, '📊')
    
    def test_webhooks(self):
        """Test webhook configurations."""
        test_data = {
            'roi': 0.25,
            'trades': 10,
            'pnl': 250.00,
            'test': True
        }
        
        logger.info("Testing webhook configurations...")
        
        if self.discord_webhook:
            try:
                self.send_alert(
                    AlertType.INFO,
                    "Test alert from PhaseGrid - Discord webhook is working! 🎯",
                    test_data
                )
                logger.info("Discord webhook test successful")
            except Exception as e:
                logger.error(f"Discord webhook test failed: {e}")
        
        if self.slack_webhook:
            try:
                self.send_alert(
                    AlertType.INFO,
                    "Test alert from PhaseGrid - Slack webhook is working! 🎯",
                    test_data
                )
                logger.info("Slack webhook test successful")
            except Exception as e:
                logger.error(f"Slack webhook test failed: {e}")
        
        if not self.discord_webhook and not self.slack_webhook:
            logger.warning("No webhooks configured to test")


# Example usage and testing
if __name__ == "__main__":
    # Set up test logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Initialize alert system
    alert_system = AlertSystem()
    
    # Test webhooks if configured
    alert_system.test_webhooks()
    
    # Example alerts
    alert_system.send_alert(
        AlertType.HIGH_ROI,
        "Daily ROI exceeded 20% threshold!",
        {'roi': 0.23, 'pnl': 230.00, 'trades': 8}
    )
    
    alert_system.send_alert(
        AlertType.ERROR,
        "Failed to connect to database",
        {'error': 'Connection timeout', 'retry_count': 3}
    )
