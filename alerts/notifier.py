"""Alert notification system with centralized secret management."""
import os
import sys
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
        # Mission-critical: Google Service Account for Sheets
        google_sa_json = os.getenv('GOOGLE_SA_JSON')
        if not google_sa_json:
            logger.error("GOOGLE_SA_JSON not found - cannot authenticate with Sheets")
            if not os.getenv('TESTING', '').lower() == 'true':
                # Only exit in production, not during tests
                sys.exit(1)
        
        # Discord configuration
        self.discord_webhook = get_secret("DISCORD_WEBHOOK_URL", "https://discord.mock/webhook")
        if 'mock' in self.discord_webhook:
            logger.warning("Using mock Discord webhook - secrets may not be loaded")
        
        # Slack configuration
        self.slack_webhook = get_secret("SLACK_WEBHOOK_URL", "https://slack.mock/webhook")
        if 'mock' in self.slack_webhook:
            logger.warning("Using mock Slack webhook - secrets may not be loaded")

        # Twilio SMS configuration
        self.twilio_account_sid = get_secret("TWILIO_SID", "mock-twilio-sid")
        self.twilio_auth_token = get_secret("TWILIO_AUTH", "mock-twilio-auth")
        self.twilio_phone_from = get_secret("TWILIO_FROM", "+1234567890")
        self.twilio_phone_to = get_secret("PHONE_TO", "+0987654321")

        # Initialize Twilio client (will be None if using mocks)
        self.twilio_client = None
        if not any(x in [self.twilio_account_sid, self.twilio_auth_token] for x in ["mock", None]):
            try:
                self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Twilio client: {e}")

    def send_discord_alert(self, message: str, username: str = "WNBA Bot") -> bool:
        """Send alert to Discord channel."""
        if "mock" in self.discord_webhook:
            logger.info(f"[MOCK] Would send Discord alert: {message}")
            return True

        try:
            payload = {
                "content": message,
                "username": username
            }
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Discord alert sent successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
            return False

    def send_slack_alert(
        self,
        message: str,
        channel: Optional[str] = None,
        username: str = "WNBA Bot"
    ) -> bool:
        """Send alert to Slack channel."""
        if "mock" in self.slack_webhook:
            logger.info(f"[MOCK] Would send Slack alert: {message}")
            return True

        try:
            payload = {
                "text": message,
                "username": username
            }
            if channel:
                payload["channel"] = channel

            response = requests.post(self.slack_webhook, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Slack alert sent successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False

    def send_sms_alert(self, message: str, to_number: Optional[str] = None) -> bool:
        """Send SMS alert via Twilio."""
        if not self.twilio_client:
            logger.info(f"[MOCK] Would send SMS: {message}")
            return True

        try:
            to_phone = to_number or self.twilio_phone_to
            sms = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone_from,
                to=to_phone
            )
            logger.info(f"SMS sent successfully: {sms.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False

    def send_all_alerts(self, message: str, include_sms: bool = True) -> Dict[str, bool]:
        """Send alert through all configured channels."""
        results = {
            "discord": self.send_discord_alert(message),
            "slack": self.send_slack_alert(message)
        }
        
        if include_sms:
            results["sms"] = self.send_sms_alert(message)
            
        logger.info(f"Alert results: {results}")
        return results

    def send_error_alert(self, error_message: str) -> Dict[str, bool]:
        """Send high-priority error alert."""
        formatted_message = f"🚨 ERROR: {error_message}"
        return self.send_all_alerts(formatted_message, include_sms=True)

    def send_success_alert(self, success_message: str) -> Dict[str, bool]:
        """Send success notification."""
        formatted_message = f"✅ SUCCESS: {success_message}"
        # Don't include SMS for success messages to avoid spam
        return self.send_all_alerts(formatted_message, include_sms=False)