"""
Test webhook configurations for Discord and Slack
"""
import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_discord_webhook():
    """Test Discord webhook configuration"""
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL not found in .env file")
        return False
    
    if webhook_url == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        print("❌ DISCORD_WEBHOOK_URL is still a placeholder")
        return False
    
    # Test message
    message = {
        "content": f"🧪 PhaseGrid Test Message - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "embeds": [{
            "title": "Webhook Test",
            "description": "This is a test message from PhaseGrid Paper Trading system",
            "color": 5814783,  # Blue color
            "fields": [
                {"name": "Status", "value": "✅ Working", "inline": True},
                {"name": "Type", "value": "Test", "inline": True}
            ]
        }]
    }
    
    try:
        response = requests.post(webhook_url, json=message)
        if response.status_code == 204:
            print("✅ Discord webhook test successful!")
            return True
        else:
            print(f"❌ Discord webhook test failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Discord webhook test error: {e}")
        return False

def test_slack_webhook():
    """Test Slack webhook configuration"""
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    
    if not webhook_url:
        print("❌ SLACK_WEBHOOK_URL not found in .env file")
        return False
    
    if webhook_url == "YOUR_SLACK_WEBHOOK_URL_HERE":
        print("❌ SLACK_WEBHOOK_URL is still a placeholder")
        return False
    
    # Test message
    message = {
        "text": f"🧪 PhaseGrid Test Message - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "attachments": [{
            "color": "good",
            "title": "Webhook Test",
            "text": "This is a test message from PhaseGrid Paper Trading system",
            "fields": [
                {"title": "Status", "value": "✅ Working", "short": True},
                {"title": "Type", "value": "Test", "short": True}
            ]
        }]
    }
    
    try:
        response = requests.post(webhook_url, json=message)
        if response.status_code == 200:
            print("✅ Slack webhook test successful!")
            return True
        else:
            print(f"❌ Slack webhook test failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Slack webhook test error: {e}")
        return False

def simulate_high_roi_alert():
    """Simulate a HIGH ROI alert"""
    print("\n📈 Simulating HIGH ROI Alert...")
    
    discord_url = os.getenv('DISCORD_WEBHOOK_URL')
    slack_url = os.getenv('SLACK_WEBHOOK_URL')
    
    alert_data = {
        "date": datetime.now().strftime('%Y-%m-%d'),
        "roi": 25.5,
        "profit": 255.0,
        "bets_won": 8,
        "bets_placed": 10
    }
    
    # Discord alert
    if discord_url and discord_url != "YOUR_DISCORD_WEBHOOK_URL_HERE":
        discord_message = {
            "content": "🚨 **HIGH ROI ALERT** 🚨",
            "embeds": [{
                "title": "Exceptional Performance Detected",
                "color": 65280,  # Green
                "fields": [
                    {"name": "ROI", "value": f"{alert_data['roi']}%", "inline": True},
                    {"name": "Profit", "value": f"${alert_data['profit']}", "inline": True},
                    {"name": "Win Rate", "value": f"{alert_data['bets_won']}/{alert_data['bets_placed']}", "inline": True}
                ]
            }]
        }
        try:
            requests.post(discord_url, json=discord_message)
            print("  ✅ HIGH ROI alert sent to Discord")
        except:
            print("  ❌ Failed to send HIGH ROI alert to Discord")
    
    # Slack alert
    if slack_url and slack_url != "YOUR_SLACK_WEBHOOK_URL_HERE":
        slack_message = {
            "text": "🚨 HIGH ROI ALERT - Exceptional Performance Detected",
            "attachments": [{
                "color": "good",
                "fields": [
                    {"title": "ROI", "value": f"{alert_data['roi']}%", "short": True},
                    {"title": "Profit", "value": f"${alert_data['profit']}", "short": True}
                ]
            }]
        }
        try:
            requests.post(slack_url, json=slack_message)
            print("  ✅ HIGH ROI alert sent to Slack")
        except:
            print("  ❌ Failed to send HIGH ROI alert to Slack")

def simulate_low_roi_alert():
    """Simulate a LOW ROI alert"""
    print("\n📉 Simulating LOW ROI Alert...")
    
    discord_url = os.getenv('DISCORD_WEBHOOK_URL')
    slack_url = os.getenv('SLACK_WEBHOOK_URL')
    
    alert_data = {
        "date": datetime.now().strftime('%Y-%m-%d'),
        "roi": -22.3,
        "loss": -223.0,
        "bets_won": 2,
        "bets_placed": 10
    }
    
    # Discord alert
    if discord_url and discord_url != "YOUR_DISCORD_WEBHOOK_URL_HERE":
        discord_message = {
            "content": "⚠️ **LOW ROI WARNING** ⚠️",
            "embeds": [{
                "title": "Poor Performance Detected",
                "color": 16711680,  # Red
                "fields": [
                    {"name": "ROI", "value": f"{alert_data['roi']}%", "inline": True},
                    {"name": "Loss", "value": f"${alert_data['loss']}", "inline": True},
                    {"name": "Win Rate", "value": f"{alert_data['bets_won']}/{alert_data['bets_placed']}", "inline": True}
                ]
            }]
        }
        try:
            requests.post(discord_url, json=discord_message)
            print("  ✅ LOW ROI alert sent to Discord")
        except:
            print("  ❌ Failed to send LOW ROI alert to Discord")
    
    # Slack alert
    if slack_url and slack_url != "YOUR_SLACK_WEBHOOK_URL_HERE":
        slack_message = {
            "text": "⚠️ LOW ROI WARNING - Poor Performance Detected",
            "attachments": [{
                "color": "danger",
                "fields": [
                    {"title": "ROI", "value": f"{alert_data['roi']}%", "short": True},
                    {"title": "Loss", "value": f"${alert_data['loss']}", "short": True}
                ]
            }]
        }
        try:
            requests.post(slack_url, json=slack_message)
            print("  ✅ LOW ROI alert sent to Slack")
        except:
            print("  ❌ Failed to send LOW ROI alert to Slack")

if __name__ == "__main__":
    print("=== PhaseGrid Webhook Test ===\n")
    
    # Test basic connectivity
    discord_ok = test_discord_webhook()
    slack_ok = test_slack_webhook()
    
    # If at least one webhook is configured, test alerts
    if discord_ok or slack_ok:
        simulate_high_roi_alert()
        simulate_low_roi_alert()
        print("\n✅ Webhook testing complete!")
    else:
        print("\n⚠️ No webhooks configured. Please add webhook URLs to your .env file:")
        print("  DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...")
        print("  SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...")