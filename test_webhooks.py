import os
import requests
import json

discord_url = os.environ.get("DISCORD_WEBHOOK_URL", "")
slack_url = os.environ.get("SLACK_WEBHOOK_URL", "")

# Test Discord
if discord_url and discord_url != "mock-discord-webhook":
    response = requests.post(discord_url, json={"content": "✅ PhaseGrid Test - Discord Working!"})
    print(f"Discord: {response.status_code}")

# Test Slack  
if slack_url and slack_url != "mock-slack-webhook":
    response = requests.post(slack_url, json={"text": "✅ PhaseGrid Test - Slack Working!"})
    print(f"Slack: {response.status_code}")
