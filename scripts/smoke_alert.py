#!/usr/bin/env python
"""
Smoke test script for PhaseGrid alert channels.
Usage:
    python scripts/smoke_alert.py --discord
    python scripts/smoke_alert.py --slack
    python scripts/smoke_alert.py --discord --slack
"""

import argparse
import sys
import os
from datetime import datetime

# Add parent directory to path to import alerts module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alerts.notifier import send_discord_alert, send_slack_alert


def test_discord():
    """Test Discord alert channel."""
    try:
        test_message = f"Test Discord alert from PhaseGrid - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        # Fixed: removed alert_type parameter
        result = send_discord_alert(test_message)
        if result:
            print("? Discord test passed")
            return True
        else:
            print("? Discord test failed - check logs above")
            return False
    except Exception as e:
        print(f"? Discord test failed with exception: {e}")
        return False


def test_slack():
    """Test Slack alert channel."""
    try:
        test_message = f"Test Slack alert from PhaseGrid - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        # Fixed: removed channel parameter
        result = send_slack_alert(test_message)
        if result:
            print("? Slack test passed")
            return True
        else:
            print("? Slack test failed - check logs above")
            return False
    except Exception as e:
        print(f"? Slack test failed with exception: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Test PhaseGrid alert channels')
    parser.add_argument('--discord', action='store_true', help='Test Discord alerts')
    parser.add_argument('--slack', action='store_true', help='Test Slack alerts')

    args = parser.parse_args()

    if not args.discord and not args.slack:
        print("Error: Please specify at least one channel to test (--discord or --slack)")
        print("Usage: python scripts/smoke_alert.py --discord --slack")
        return 1

    all_passed = True

    if args.discord:
        print("Testing Discord alerts...")
        if not test_discord():
            all_passed = False

    if args.slack:
        print("Testing Slack alerts...")
        if not test_slack():
            all_passed = False

    if all_passed:
        print("\n? All tests passed!")
    else:
        print("\n? Some tests failed. Check the output above for details.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
