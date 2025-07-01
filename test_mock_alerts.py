import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alerts.notifier import get_secret, AlertNotifier

# Test the get_secret function
print("Testing get_secret function:")
print(f"DISCORD_WEBHOOK_URL: {get_secret('DISCORD_WEBHOOK_URL')}")
print(f"PHONE_TO: {get_secret('PHONE_TO')}")
print(f"Custom default: {get_secret('NONEXISTENT_VAR', 'my-custom-default')}")

# Test the notifier in mock mode
print("\nTesting AlertNotifier in mock mode:")
notifier = AlertNotifier()
results = notifier.send_all_alerts(
    title="Mock Test",
    message="Testing mock alerts",
    details={"Mode": "Mock", "Purpose": "Testing"}
)
print(f"Results: {results}")
