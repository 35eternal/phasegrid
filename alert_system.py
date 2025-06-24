#!/usr/bin/env python3
"""Alert system for PhaseGrid - SMS via Twilio and Discord webhooks."""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

logger = logging.getLogger(__name__)

class AlertManager:
    """Manages SMS and Discord alerts for betting results."""
    
    def __init__(self):
        """Initialize alert manager with credentials from environment."""
        # Twilio configuration
        self.twilio_sid = os.getenv('TWILIO_SID')
        self.twilio_auth = os.getenv('TWILIO_AUTH')
        self.twilio_from = os.getenv('TWILIO_FROM')
        self.phone_to = os.getenv('PHONE_TO', '').split(',')  # Comma-separated list
        
        # Discord configuration (optional)
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
        
        # Initialize Twilio client if credentials available
        self.twilio_client = None
        if self.twilio_sid and self.twilio_auth:
            try:
                self.twilio_client = Client(self.twilio_sid, self.twilio_auth)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio: {e}")
    
    def send_grading_complete(self, results: Dict[str, Any]):
        """Send alert when grading is complete."""
        # Calculate summary stats
        total_slips = results.get('total', 0)
        wins = results.get('wins', 0)
        losses = results.get('losses', 0)
        pushes = results.get('pushes', 0)
        profit = results.get('profit', 0.0)
        
        if total_slips == 0:
            logger.info("No slips to grade")
            return
        
        win_rate = (wins / total_slips) * 100 if total_slips > 0 else 0
        
        # Create message
        message = f"""📊 PhaseGrid Results - {datetime.now().strftime('%Y-%m-%d')}

Slips Graded: {total_slips}
✅ Wins: {wins} ({win_rate:.1f}%)
❌ Losses: {losses}
🔄 Pushes: {pushes}
💰 Profit: ${profit:+.2f}

Win Rate: {win_rate:.1f}%"""

        # Send alerts
        if win_rate >= 70 or win_rate <= 30 or abs(profit) > 500:
            # High priority - send SMS
            self._send_sms_alert(message, priority='high')
        
        # Always send to Discord if configured
        self._send_discord_alert(message, win_rate)
        
        # Log the results
        logger.info(f"Grading complete: {total_slips} slips, {win_rate:.1f}% win rate, ${profit:+.2f} profit")
    
    def send_high_confidence_alert(self, slips: List[Dict[str, Any]]):
        """Alert for high confidence betting opportunities."""
        if not slips:
            return
            
        # Filter for very high confidence
        high_conf_slips = [s for s in slips if s.get('confidence', 0) >= 0.85]
        
        if not high_conf_slips:
            return
        
        message = f"🔥 HIGH CONFIDENCE ALERTS - {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        for slip in high_conf_slips[:5]:  # Top 5 only
            message += f"• {slip['player']} - {slip['prop_type']} {slip['pick']} {slip['line']}\n"
            message += f"  Confidence: {slip['confidence']:.0%}\n"
            message += f"  Reasoning: {slip['reasoning']}\n\n"
        
        # Send high priority alert
        self._send_sms_alert(message, priority='high')
        self._send_discord_alert(message, color=0xFF0000)  # Red for high priority
    
    def send_daily_summary(self, stats: Dict[str, Any]):
        """Send daily performance summary."""
        message = f"""📈 Daily Summary - {datetime.now().strftime('%Y-%m-%d')}

Week Stats:
• Slips: {stats.get('week_total', 0)}
• Win Rate: {stats.get('week_win_rate', 0):.1f}%
• ROI: {stats.get('week_roi', 0):+.1f}%
• Profit: ${stats.get('week_profit', 0):+.2f}

Month Stats:
• Slips: {stats.get('month_total', 0)}
• Win Rate: {stats.get('month_win_rate', 0):.1f}%
• ROI: {stats.get('month_roi', 0):+.1f}%
• Profit: ${stats.get('month_profit', 0):+.2f}

Best Performers:
{self._format_best_performers(stats.get('best_performers', []))}"""

        self._send_discord_alert(message, color=0x00FF00)  # Green for summary
        
        # Only SMS if exceptional performance
        if stats.get('week_roi', 0) > 20 or stats.get('week_roi', 0) < -20:
            self._send_sms_alert(f"Weekly ROI: {stats.get('week_roi', 0):+.1f}%! Check Discord for details.")
    
    def send_error_alert(self, error: str, critical: bool = False):
        """Send error alert to administrators."""
        message = f"⚠️ PhaseGrid Error - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{error}"
        
        if critical:
            # Critical errors go to SMS
            self._send_sms_alert(message, priority='critical')
        
        # All errors go to Discord
        self._send_discord_alert(message, color=0xFFFF00)  # Yellow for errors
    
    def _send_sms_alert(self, message: str, priority: str = 'normal') -> bool:
        """Send SMS alert via Twilio."""
        if not self.twilio_client or not self.phone_to:
            logger.warning("SMS alerts not configured")
            return False
        
        success_count = 0
        
        for phone in self.phone_to:
            if not phone.strip():
                continue
                
            try:
                # Truncate message for SMS (160 char segments)
                sms_message = message[:1000] if len(message) > 1000 else message
                
                # Add priority prefix
                if priority == 'critical':
                    sms_message = "🚨 CRITICAL: " + sms_message
                elif priority == 'high':
                    sms_message = "⚡ ALERT: " + sms_message
                
                # Send SMS
                msg = self.twilio_client.messages.create(
                    body=sms_message,
                    from_=self.twilio_from,
                    to=phone.strip()
                )
                
                logger.info(f"SMS sent to {phone}: {msg.sid}")
                success_count += 1
                
            except TwilioException as e:
                logger.error(f"Twilio error sending to {phone}: {e}")
            except Exception as e:
                logger.error(f"Failed to send SMS to {phone}: {e}")
        
        return success_count > 0
    
    def _send_discord_alert(self, message: str, color: int = 0x0099FF, win_rate: float = None) -> bool:
        """Send alert to Discord webhook."""
        if not self.discord_webhook:
            logger.debug("Discord webhook not configured")
            return False
        
        try:
            # Determine color based on win rate if provided
            if win_rate is not None:
                if win_rate >= 60:
                    color = 0x00FF00  # Green
                elif win_rate >= 50:
                    color = 0x0099FF  # Blue
                else:
                    color = 0xFF0000  # Red
            
            # Create Discord embed
            embed = {
                "embeds": [{
                    "description": message,
                    "color": color,
                    "timestamp": datetime.utcnow().isoformat(),
                    "footer": {
                        "text": "PhaseGrid Alerts"
                    }
                }]
            }
            
            # Send to Discord
            response = requests.post(self.discord_webhook, json=embed)
            response.raise_for_status()
            
            logger.info("Discord alert sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
            return False
    
    def _format_best_performers(self, performers: List[Dict[str, Any]]) -> str:
        """Format best performers for display."""
        if not performers:
            return "No data available"
        
        lines = []
        for p in performers[:3]:  # Top 3
            lines.append(f"• {p['player']}: {p['win_rate']:.1f}% ({p['wins']}/{p['total']})")
        
        return '\n'.join(lines)

# Utility functions for quick alerts
def send_quick_sms(message: str):
    """Send a quick SMS alert."""
    manager = AlertManager()
    return manager._send_sms_alert(message)

def send_quick_discord(message: str, color: int = 0x0099FF):
    """Send a quick Discord alert."""
    manager = AlertManager()
    return manager._send_discord_alert(message, color)

def main():
    """Test the alert system."""
    manager = AlertManager()
    
    # Test grading complete alert
    test_results = {
        'total': 10,
        'wins': 7,
        'losses': 3,
        'pushes': 0,
        'profit': 250.50
    }
    
    manager.send_grading_complete(test_results)
    
    # Test high confidence alert
    test_slips = [{
        'player': 'A\'ja Wilson',
        'prop_type': 'points',
        'pick': 'over',
        'line': 25.5,
        'confidence': 0.87,
        'reasoning': 'Peak phase; averaging 28.3 last 5 games'
    }]
    
    manager.send_high_confidence_alert(test_slips)

if __name__ == "__main__":
    main()