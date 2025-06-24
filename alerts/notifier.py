"""
Twilio Notification Service with 10DLC Support
Handles SMS alerts for betting recommendations
"""
import os
import logging
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
            to_number: Recipient phone number (E.164 format)
            message: Message content
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Twilio not enabled, skipping SMS")
            return False
        
        try:
            # Apply A2P compliance for 10DLC if needed
            if self.is_local:
                # Add opt-out instructions for 10DLC compliance
                if "STOP" not in message.upper():
                    message += "\n\nReply STOP to unsubscribe"
            
            message_obj = self.client.messages.create(
                body=message,
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
    
    def send_bulk_sms(self, recipients: List[str], message: str) -> Dict[str, bool]:
        """
        Send SMS to multiple recipients
        
        Args:
            recipients: List of phone numbers
            message: Message content
            
        Returns:
            Dictionary mapping phone numbers to success status
        """
        results = {}
        
        for recipient in recipients:
            results[recipient] = self.send_sms(recipient, message)
        
        return results
    
    def format_predictions_message(self, predictions: List[Dict[str, Any]], max_length: int = 1600) -> str:
        """
        Format predictions into SMS-friendly message
        
        Args:
            predictions: List of prediction dictionaries
            max_length: Maximum message length
            
        Returns:
            Formatted message string
        """
        if not predictions:
            return "No predictions available today."
        
        # Sort by edge percentage
        predictions.sort(key=lambda x: abs(x.get("edge_pct", 0)), reverse=True)
        
        lines = ["🏀 Today's Top Plays:"]
        
        for i, pred in enumerate(predictions[:5], 1):  # Top 5 only
            player = pred.get("player", "Unknown")
            prop = pred.get("prop_type", "")
            line = pred.get("line", 0)
            edge = pred.get("edge_pct", 0)
            rec = pred.get("recommendation", "")
            
            line_text = f"{i}. {player} {rec} {line} {prop} ({edge:+.1f}%)"
            
            # Check if adding this line would exceed limit
            current_length = sum(len(l) for l in lines) + len(lines)
            if current_length + len(line_text) > max_length - 50:  # Leave room for opt-out
                break
                
            lines.append(line_text)
        
        return "\n".join(lines)


# Singleton instance for easy import
notifier = TwilioNotifier()


def send_prediction_alerts(predictions: List[Dict[str, Any]], recipients: List[str]) -> bool:
    """
    Convenience function to send prediction alerts
    
    Args:
        predictions: List of predictions
        recipients: List of phone numbers to notify
        
    Returns:
        True if all messages sent successfully
    """
    if not notifier.enabled:
        logger.warning("Notifications disabled")
        return False
    
    message = notifier.format_predictions_message(predictions)
    results = notifier.send_bulk_sms(recipients, message)
    
    success_count = sum(results.values())
    logger.info(f"Sent {success_count}/{len(recipients)} notifications successfully")
    
    return success_count == len(recipients)


if __name__ == "__main__":
    # Test notification
    test_predictions = [
        {
            "player": "Test Player",
            "prop_type": "Points",
            "line": 20.5,
            "edge_pct": 5.2,
            "recommendation": "OVER"
        }
    ]
    
    if notifier.enabled:
        message = notifier.format_predictions_message(test_predictions)
        print(f"Test message:\n{message}")
    else:
        print("Twilio not configured")