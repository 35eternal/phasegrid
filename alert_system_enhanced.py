#!/usr/bin/env python3
"""Enhanced alert system for PhaseGrid - SMS via Twilio and Discord webhooks."""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import json
import time

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

        # Discord configuration
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
        
        # Slack configuration (optional)
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        
        # Alert configuration
        self.max_retries = int(os.getenv('ALERT_MAX_RETRIES', '3'))
        self.base_delay = float(os.getenv('ALERT_BASE_DELAY', '1.0'))
        self.max_delay = float(os.getenv('ALERT_MAX_DELAY', '60.0'))

        # Initialize Twilio client if credentials available
        self.twilio_client = None
        if self.twilio_sid and self.twilio_auth:
            try:
                self.twilio_client = Client(self.twilio_sid, self.twilio_auth)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio: {e}")

    def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries - 1:
                    logger.error(f"Max retries exceeded for {func.__name__}: {e}")
                    raise
                
                # Calculate delay with exponential backoff
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                time.sleep(delay)
        
        if last_exception:
            raise last_exception

    def send_sms(self, message: str, numbers: Optional[List[str]] = None):
        """Send SMS alert via Twilio."""
        if not self.twilio_client:
            logger.warning("Twilio client not initialized, skipping SMS")
            return
        
        numbers = numbers or self.phone_to
        
        for number in numbers:
            if not number.strip():
                continue
                
            try:
                self._retry_with_backoff(
                    self.twilio_client.messages.create,
                    body=message[:1600],  # SMS limit
                    from_=self.twilio_from,
                    to=number.strip()
                )
                logger.info(f"SMS sent to {number}")
            except Exception as e:
                logger.error(f"Failed to send SMS to {number}: {e}")

    def send_discord(self, message: str, embed: Optional[Dict] = None):
        """Send alert to Discord webhook."""
        if not self.discord_webhook:
            logger.warning("Discord webhook not configured, skipping")
            return
        
        try:
            payload = {"content": message[:2000]}  # Discord limit
            
            if embed:
                payload["embeds"] = [embed]
            
            response = self._retry_with_backoff(
                requests.post,
                self.discord_webhook,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 204:
                logger.info("Discord alert sent successfully")
            else:
                logger.error(f"Discord webhook failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")

    def send_slack(self, message: str, attachments: Optional[List[Dict]] = None):
        """Send alert to Slack webhook."""
        if not self.slack_webhook:
            logger.debug("Slack webhook not configured, skipping")
            return
        
        try:
            payload = {"text": message}
            
            if attachments:
                payload["attachments"] = attachments
            
            response = self._retry_with_backoff(
                requests.post,
                self.slack_webhook,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Slack alert sent successfully")
            else:
                logger.error(f"Slack webhook failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

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
        
        # Format message
        message = (
            f"📊 PhaseGrid Grading Complete\n"
            f"Date: {results.get('date', 'Unknown')}\n"
            f"Total Slips: {total_slips}\n"
            f"Wins: {wins} ({win_rate:.1f}%)\n"
            f"Losses: {losses}\n"
            f"Pushes: {pushes}\n"
            f"Profit: ${profit:,.2f}"
        )
        
        # Send to all channels
        self.send_sms(message)
        
        # Discord embed
        embed = {
            "title": "📊 PhaseGrid Daily Results",
            "color": 0x00ff00 if profit > 0 else 0xff0000,
            "fields": [
                {"name": "Date", "value": results.get('date', 'Unknown'), "inline": True},
                {"name": "Total Slips", "value": str(total_slips), "inline": True},
                {"name": "Win Rate", "value": f"{win_rate:.1f}%", "inline": True},
                {"name": "Wins", "value": str(wins), "inline": True},
                {"name": "Losses", "value": str(losses), "inline": True},
                {"name": "Pushes", "value": str(pushes), "inline": True},
                {"name": "Profit", "value": f"${profit:,.2f}", "inline": False}
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        self.send_discord(message, embed)
        
        # Slack attachment
        color = "good" if profit > 0 else "danger"
        attachment = {
            "color": color,
            "title": "PhaseGrid Daily Results",
            "fields": [
                {"title": "Date", "value": results.get('date', 'Unknown'), "short": True},
                {"title": "Total Slips", "value": str(total_slips), "short": True},
                {"title": "Win Rate", "value": f"{win_rate:.1f}%", "short": True},
                {"title": "Profit", "value": f"${profit:,.2f}", "short": True}
            ],
            "footer": "PhaseGrid",
            "ts": int(datetime.utcnow().timestamp())
        }
        self.send_slack(message, [attachment])

    def send_critical_alert(self, message: str):
        """Send critical alert through all available channels."""
        logger.critical(f"CRITICAL ALERT: {message}")
        
        # Add urgency indicators
        urgent_message = f"🚨 CRITICAL ALERT 🚨\n{message}\n\nRequires immediate attention!"
        
        # Send to all channels with high priority
        self.send_sms(urgent_message)
        
        # Discord with @everyone mention if configured
        discord_message = f"@everyone\n{urgent_message}"
        embed = {
            "title": "🚨 CRITICAL SYSTEM ALERT",
            "description": message,
            "color": 0xff0000,  # Red
            "footer": {"text": "PhaseGrid Alert System"},
            "timestamp": datetime.utcnow().isoformat()
        }
        self.send_discord(discord_message, embed)
        
        # Slack with @channel mention
        slack_message = f"<!channel>\n{urgent_message}"
        attachment = {
            "color": "danger",
            "title": "CRITICAL SYSTEM ALERT",
            "text": message,
            "footer": "PhaseGrid Alert System",
            "ts": int(datetime.utcnow().timestamp())
        }
        self.send_slack(slack_message, [attachment])

    def send_daily_summary(self, metrics: Dict[str, Any]):
        """Send daily summary metrics."""
        date = metrics.get('date', 'Unknown')
        slip_count = metrics.get('slip_count', 0)
        avg_confidence = metrics.get('average_confidence', 0)
        
        message = (
            f"📈 PhaseGrid Daily Summary\n"
            f"Date: {date}\n"
            f"Slips Generated: {slip_count}\n"
            f"Avg Confidence: {avg_confidence:.2%}\n"
            f"High Confidence: {metrics.get('high_confidence_count', 0)}\n"
            f"Low Confidence: {metrics.get('low_confidence_count', 0)}"
        )
        
        # Only send summary to Discord/Slack, not SMS
        embed = {
            "title": "📈 Daily Summary",
            "color": 0x0099ff,
            "fields": [
                {"name": "Date", "value": date, "inline": True},
                {"name": "Total Slips", "value": str(slip_count), "inline": True},
                {"name": "Avg Confidence", "value": f"{avg_confidence:.2%}", "inline": True}
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        self.send_discord(message, embed)
        self.send_slack(message)

    def test_alerts(self):
        """Test all configured alert channels."""
        test_message = (
            f"🧪 PhaseGrid Alert Test\n"
            f"Timestamp: {datetime.utcnow().isoformat()}\n"
            f"All systems operational!"
        )
        
        logger.info("Testing all alert channels...")
        
        # Test each channel
        if self.twilio_client:
            self.send_sms(test_message)
        if self.discord_webhook:
            self.send_discord(test_message)
        if self.slack_webhook:
            self.send_slack(test_message)
        
        logger.info("Alert test complete!")