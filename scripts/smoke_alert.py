#!/usr/bin/env python3
"""
Smoke test script for PhaseGrid alert channels.
Usage:
    python scripts/smoke_alert.py --sms
    python scripts/smoke_alert.py --discord
    python scripts/smoke_alert.py --slack
    python scripts/smoke_alert.py --sms --discord --slack
"""

import argparse
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alerts.notifier import send_sms, send_discord_alert, send_slack_alert


def test_sms():
    """Test SMS alert channel."""
    try:
        test_message = f"Test SMS from PhaseGrid - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        result = send_sms(test_message)
        if result:
            print("✅ SMS test passed")
            return True
        else:
            print("❌ SMS test failed - check logs above")
            return False
    except Exception as e:
        print(f"❌ SMS test failed with exception: {e}")
        return False


def test_discord():
    """Test Discord alert channel."""
    try:
        test_message = f"🧪 Test alert from PhaseGrid - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        result = send_discord_alert(test_message)
        if result:
            print("✅ Discord test passed")
            return True
        else:
            print("❌ Discord test failed - check logs above")
            return False
    except Exception as e:
        print(f"❌ Discord test failed with exception: {e}")
        return False


def test_slack():
    """Test Slack alert channel."""
    try:
        test_message = f"🧪 Test alert from PhaseGrid - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        result = send_slack_alert(test_message)
        if result:
            print("✅ Slack test passed")
            return True
        else:
            print("❌ Slack test failed - check logs above")
            return False
    except Exception as e:
        print(f"❌ Slack test failed with exception: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Test PhaseGrid alert channels')
    parser.add_argument('--sms', action='store_true', help='Test SMS alerts')
    parser.add_argument('--discord', action='store_true', help='Test Discord alerts')
    parser.add_argument('--slack', action='store_true', help='Test Slack alerts')

    args = parser.parse_args()

    if not args.sms and not args.discord and not args.slack:
        print("Error: Please specify at least one channel to test (--sms or --discord or --slack)")
        print("Usage: python scripts/smoke_alert.py --sms --discord --slack")
        return 1

    all_passed = True

    if args.sms:
        print("Testing SMS alerts...")
        if not test_sms():
            all_passed = False

    if args.discord:
        print("Testing Discord alerts...")
        if not test_discord():
            all_passed = False
            
    if args.slack:
        print("Testing Slack alerts...")
        if not test_slack():
            all_passed = False

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
