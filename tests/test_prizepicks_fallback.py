"""
Notification Service with Discord and Slack Support
Handles alerts for betting recommendations
"""
import os
import logging
import requests
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Discord configuration
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# Load Slack configuration  
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# SMS is disabled for now (Twilio requires 10DLC registration)
SMS_ENABLED = False


def send_sms(message: str, to_number: str = None) -> bool:
    """
    SMS alerts are currently disabled
    
    Args:
        message: Message to send
        to_number: Recipient phone number
        
    Returns:
        bool: Always False (SMS disabled)
    """
    logger.debug("SMS notifications are disabled (Twilio 10DLC registration required)")
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
        webhook_url = SLACK_WEBHOOK_URL

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


# For backward compatibility - keeping the Twilio class but disabled
class TwilioNotifier:
    """Placeholder for SMS notifications (currently disabled)"""
    
    def __init__(self):
        self.enabled = False
        
    def send_sms(self, to_number: str, message: str) -> bool:
        """SMS is disabled"""
        return False


# Singleton instance
_notifier = TwilioNotifier()

def get_notifier():
    """Get the notifier instance"""
    return _notifier


# For backward compatibility
if __name__ == "__main__":
    # Test the notifier
    import sys
    if len(sys.argv) > 1:
        test_message = sys.argv[1]
    else:
        test_message = "Test alert from PhaseGrid"

    print(f"Testing Discord...")
    discord_result = send_discord_alert(test_message)
    print(f"Discord result: {discord_result}")
    
    print(f"\nTesting Slack...")
    slack_result = send_slack_alert(test_message)
    print(f"Slack result: {slack_result}")
    
    print(f"\nSMS is currently disabled (Twilio 10DLC registration required)")