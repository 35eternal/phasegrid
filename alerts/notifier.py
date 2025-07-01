"""Alert notification system with centralized secret management."""
import os
import logging
from typing import Optional, Dict, Any
import requests
from twilio.rest import Client

logger = logging.getLogger(__name__)


def get_secret(name: str, default: str = "mock-value") -> str:
    """
    Centralized secret retrieval with fallback to mock values.
    
    This allows tests and CI to run without real credentials while
    still maintaining the ability to use real credentials in production.
    
    Args:
        name: The environment variable name
        default: Default value if not found (defaults to "mock-value")
        
    Returns:
        The secret value or the default
    """
    value = os.getenv(name, default)
    
    # Log when using mock values (but don't log real values!)
    if value == default:
        logger.debug(f"Using mock value for {name}")
    else:
        logger.debug(f"Using real value for {name}")
    
    return value


class AlertNotifier:
    """Handles sending alerts through multiple channels."""
    
    def __init__(self):
        """Initialize the notifier with credentials from environment."""
        # Discord configuration
        self.discord_webhook = get_secret("DISCORD_WEBHOOK_URL", "mock-discord-webhook")
        
        # Slack configuration
        self.slack_webhook = get_secret("SLACK_WEBHOOK_URL", "mock-slack-webhook")
        
        # Twilio SMS configuration
        self.twilio_account_sid = get_secret("TWILIO_SID", "mock-twilio-sid")
        self.twilio_auth_token = get_secret("TWILIO_AUTH", "mock-twilio-auth")
        self.twilio_phone_from = get_secret("TWILIO_FROM", "+1234567890")
        self.phone_to = get_secret("PHONE_TO", "mock")
        
        # Initialize Twilio client only if we have real credentials
        self.twilio_client = None
        if self.twilio_account_sid != "mock-twilio-sid" and self.twilio_auth_token != "mock-twilio-auth":
            try:
                self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Twilio client: {e}")
    
    def send_discord_alert(self, message: str, embed: Optional[Dict[str, Any]] = None) -> bool:
        """Send alert to Discord channel."""
        if self.discord_webhook.startswith("mock"):
            logger.info(f"[MOCK] Discord alert: {message}")
            return True
            
        try:
            payload = {"content": message}
            if embed:
                payload["embeds"] = [embed]
                
            response = requests.post(
                self.discord_webhook,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.info("Discord alert sent successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
            return False
    
    def send_slack_alert(self, message: str, blocks: Optional[list] = None) -> bool:
        """Send alert to Slack channel."""
        if self.slack_webhook.startswith("mock"):
            logger.info(f"[MOCK] Slack alert: {message}")
            return True
            
        try:
            payload = {"text": message}
            if blocks:
                payload["blocks"] = blocks
                
            response = requests.post(
                self.slack_webhook,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.info("Slack alert sent successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False
    
    def send_sms_alert(self, message: str) -> bool:
        """Send SMS alert via Twilio."""
        # Check if we're in mock mode
        if self.phone_to == "mock" or self.twilio_account_sid.startswith("mock"):
            logger.info(f"[MOCK] SMS alert to {self.phone_to}: {message}")
            return True
            
        if not self.twilio_client:
            logger.warning("Twilio client not initialized, skipping SMS")
            return False
            
        try:
            message = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone_from,
                to=self.phone_to
            )
            logger.info(f"SMS sent successfully: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS alert: {e}")
            return False
    
    def send_all_alerts(self, title: str, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
        """
        Send alerts to all configured channels.
        
        Args:
            title: Alert title
            message: Main alert message
            details: Optional additional details
            
        Returns:
            Dictionary with success status for each channel
        """
        results = {}
        
        # Format message with title
        full_message = f"**{title}**\n{message}"
        
        # Send to Discord
        discord_embed = None
        if details:
            discord_embed = {
                "title": title,
                "description": message,
                "fields": [{"name": k, "value": str(v), "inline": True} for k, v in details.items()],
                "color": 0x00ff00  # Green color
            }
        results["discord"] = self.send_discord_alert(full_message, discord_embed)
        
        # Send to Slack
        slack_blocks = None
        if details:
            slack_blocks = [
                {"type": "header", "text": {"type": "plain_text", "text": title}},
                {"type": "section", "text": {"type": "mrkdwn", "text": message}},
                {"type": "divider"},
                {"type": "section", "fields": [
                    {"type": "mrkdwn", "text": f"*{k}:*\n{v}"} for k, v in details.items()
                ]}
            ]
        results["slack"] = self.send_slack_alert(full_message, slack_blocks)
        
        # Send SMS (shorter format)
        sms_message = f"{title}: {message}"
        if len(sms_message) > 160:
            sms_message = sms_message[:157] + "..."
        results["sms"] = self.send_sms_alert(sms_message)
        
        # Log summary
        successful = [ch for ch, success in results.items() if success]
        failed = [ch for ch, success in results.items() if not success]
        
        if successful:
            logger.info(f"Alerts sent successfully to: {', '.join(successful)}")
        if failed:
            logger.warning(f"Failed to send alerts to: {', '.join(failed)}")
            
        return results


# Convenience function for quick alerts
def send_alert(title: str, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
    """
    Send an alert to all configured channels.
    
    This is a convenience function that creates a notifier and sends the alert.
    
    Args:
        title: Alert title
        message: Main alert message  
        details: Optional additional details
        
    Returns:
        Dictionary with success status for each channel
    """
    notifier = AlertNotifier()
    return notifier.send_all_alerts(title, message, details)


# Legacy compatibility functions
def send_discord_alert(message: str, **kwargs) -> bool:
    """Legacy function for Discord alerts."""
    notifier = AlertNotifier()
    return notifier.send_discord_alert(message)


def send_slack_alert(message: str, **kwargs) -> bool:
    """Legacy function for Slack alerts."""
    notifier = AlertNotifier()
    return notifier.send_slack_alert(message)


def send_sms(message: str, to_number: Optional[str] = None) -> bool:
    """Legacy function for SMS alerts."""
    notifier = AlertNotifier()
    if to_number and to_number != notifier.phone_to:
        # Override the default phone number if provided
        old_phone = notifier.phone_to
        notifier.phone_to = to_number
        result = notifier.send_sms_alert(message)
        notifier.phone_to = old_phone
        return result
    return notifier.send_sms_alert(message)


if __name__ == "__main__":
    # Test the alert system
    logging.basicConfig(level=logging.DEBUG)
    
    test_results = send_alert(
        title="Test Alert",
        message="This is a test of the PhaseGrid alert system",
        details={
            "Environment": "Development",
            "Timestamp": "2025-07-01 15:45:00",
            "Status": "Testing"
        }
    )
    
    print(f"Alert test results: {test_results}")