"""Test notification systems."""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test Discord webhook
def test_discord():
    """Test Discord notification."""
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("DISCORD_WEBHOOK_URL not set")
        return False
    
    import requests
    
    payload = {
        "content": "🧪 Test notification from PhaseGrid B2 - Nightly Grader verification"
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            print("✅ Discord notification sent successfully")
            return True
        else:
            print(f"❌ Discord notification failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Discord error: {e}")
        return False

# Test Slack webhook
def test_slack():
    """Test Slack notification."""
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if not webhook_url:
        print("SLACK_WEBHOOK_URL not set")
        return False
    
    import requests
    
    payload = {
        "text": "🧪 Test notification from PhaseGrid B2 - Nightly Grader verification"
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            print("✅ Slack notification sent successfully")
            return True
        else:
            print(f"❌ Slack notification failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Slack error: {e}")
        return False

if __name__ == "__main__":
    print("Testing notification systems...")
    test_discord()
    test_slack()
