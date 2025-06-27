"""
Twilio Notification Service with 10DLC Support
Handles SMS alerts for betting recommendations
"""
import os
import logging
import requests
from typing import List, Dict, Any
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Twilio configuration at module level
TWILIO_SID = os.getenv("TWILIO_SID", "")
TWILIO_AUTH = os.getenv("TWILIO_AUTH", "")
TWILIO_FROM = os.getenv("TWILIO_FROM", "")
IS_LOCAL = TWILIO_FROM.startswith("+1")  # Detect if using 10DLC local number

# Load Discord configuration
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# Validate configuration
if not all([TWILIO_SID, TWILIO_AUTH, TWILIO_FROM]):
    logger.warning("Twilio credentials not fully configured. SMS notifications will be disabled.")
    TWILIO_ENABLED = False
else:
    TWILIO_ENABLED = True
    logger.info(f"Twilio configured with {'10DLC local' if IS_LOCAL else 'toll-free'} number")


class TwilioNotifier:
    """Handles SMS notifications via Twilio"""

    def __init__(self):
        """Initialize Twilio client if credentials are available"""
        self.enabled = TWILIO_ENABLED
        self.client = None

        if self.enabled:
            try:
                self.client = Client(TWILIO_SID, TWILIO_AUTH)
                self.from_number = TWILIO_FROM
                self.is_local = IS_LOCAL
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.enabled = False

    def send_sms(self, to_number: str, message: str) -> bool:
        """
        Send SMS message
        
        Args:
            to_number: Recipient phone number
            message: Message to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            logger.warning("SMS notifications are disabled")
            return False

        try:
            message_obj = self.client.messages.create(
                body=message[:1600],  # SMS character limit
                from_=self.from_number,
                to=to_number
            )
            logger.info(f"SMS sent successfully: {message_obj.sid}")
            return True
        except TwilioRestException as e:
            logger.error(f"Twilio error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending SMS: {e}")
            return False


# Simple wrapper functions for easy use in other scripts
_notifier = None

def get_notifier():
    """Get or create the singleton notifier instance"""
    global _notifier
    if _notifier is None:
        _notifier = TwilioNotifier()
    return _notifier


def send_sms(message: str, to_number: str = None) -> bool:
    """
    Send SMS alert via Twilio
    
    Args:
        message: Message to send
        to_number: Recipient phone number (defaults to PHONE_TO env var)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if to_number is None:
            to_number = os.getenv("PHONE_TO")
            if not to_number:
                logger.error("No phone number provided and PHONE_TO not set")
                return False
        
        notifier = get_notifier()
        return notifier.send_sms(to_number, f"[PhaseGrid] {message}")
    except Exception as e:
        logger.error(f"Error in send_sms wrapper: {e}")
        return False


def send_discord_alert(message: str) -> bool:
    """
    Send alert to Discord webhook
    
    Args:
        message: Message to send
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        webhook_url = DISCORD_WEBHOOK_URL
        
        if not webhook_url:
            logger.error("DISCORD_WEBHOOK_URL not configured")
            return False
        
        payload = {
            "content": message,
            "username": "PhaseGrid Bot"
        }
        
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        
        logger.info("Discord alert sent successfully")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Discord webhook error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Discord alert: {e}")
        return False




def send_slack_alert(message: str) -> bool:
    """
    Send alert to Slack webhook
    
    Args:
        message: Message to send
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
        
        if not webhook_url:
            logger.error("SLACK_WEBHOOK_URL not configured")
            return False
        
        payload = {
            "text": message,
            "username": "PhaseGrid Bot",
            "icon_emoji": ":chart_with_upwards_trend:"
        }
        
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        
        logger.info("Slack alert sent successfully")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Slack webhook error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Slack alert: {e}")
        return False

# For backward compatibility
if __name__ == "__main__":
    # Test the notifier
    import sys
    if len(sys.argv) > 1:
        test_message = sys.argv[1]
    else:
        test_message = "Test alert from PhaseGrid"
    
    print(f"Testing SMS...")
    sms_result = send_sms(test_message)
    print(f"SMS result: {sms_result}")
    
    print(f"\nTesting Discord...")
    discord_result = send_discord_alert(test_message)
    print(f"Discord result: {discord_result}")

