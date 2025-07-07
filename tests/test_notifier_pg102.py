"""Unit tests for alert notification system - PG-102 (CI-compatible version)"""
import pytest
import os
from unittest.mock import patch, MagicMock, ANY
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alerts.notifier import (
    AlertNotifier, 
    send_sms, 
    send_discord_alert, 
    send_slack_alert,
    get_secret
)


class TestAlertNotifier:
    """Test the AlertNotifier class methods."""
    
    @patch.dict(os.environ, {
        'GOOGLE_SA_JSON': 'test-json', 
        'TESTING': 'true',
        'DISCORD_WEBHOOK_URL': '',  # Force empty to use mock
        'SLACK_WEBHOOK_URL': ''     # Force empty to use mock
    }, clear=True)
    def test_init_with_mocks(self):
        """Test initialization with mock values."""
        notifier = AlertNotifier()
        assert 'mock' in notifier.discord_webhook
        assert 'mock' in notifier.slack_webhook
        assert notifier.twilio_client is None
    
    @patch.dict(os.environ, {
        'GOOGLE_SA_JSON': 'test-json',
        'TESTING': 'true',
        'DISCORD_WEBHOOK_URL': 'https://discord.com/real-webhook',
        'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/real-webhook'
    })
    @patch('requests.post')
    def test_discord_alert_real_webhook(self, mock_post):
        """Test Discord alert with real webhook URL."""
        mock_post.return_value.status_code = 204
        
        notifier = AlertNotifier()
        result = notifier.send_discord_alert("Test message")
        
        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == 'https://discord.com/real-webhook'
        assert call_args[1]['json']['content'] == "Test message"
    
    @patch.dict(os.environ, {
        'GOOGLE_SA_JSON': 'test-json',
        'TESTING': 'true',
        'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/real-webhook'
    })
    @patch('requests.post')
    def test_slack_alert_real_webhook(self, mock_post):
        """Test Slack alert with real webhook URL."""
        mock_post.return_value.status_code = 200
        
        notifier = AlertNotifier()
        result = notifier.send_slack_alert("Test message", channel="#test")
        
        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == 'https://hooks.slack.com/real-webhook'
        assert call_args[1]['json']['text'] == "Test message"
        assert call_args[1]['json']['channel'] == "#test"
    
    @patch.dict(os.environ, {
        'GOOGLE_SA_JSON': 'test-json', 
        'TESTING': 'true',
        'TWILIO_SID': '',
        'TWILIO_AUTH': ''
    }, clear=True)
    def test_sms_mock_mode(self):
        """Test SMS in mock mode."""
        notifier = AlertNotifier()
        result = notifier.send_sms_alert("Test SMS")
        assert result is True  # Should return True in mock mode
    
    @patch.dict(os.environ, {
        'GOOGLE_SA_JSON': 'test-json', 
        'TESTING': 'true',
        'DISCORD_WEBHOOK_URL': '',
        'SLACK_WEBHOOK_URL': '',
        'TWILIO_SID': '',
        'TWILIO_AUTH': ''
    }, clear=True)
    def test_send_all_alerts(self):
        """Test sending alerts through all channels."""
        notifier = AlertNotifier()
        results = notifier.send_all_alerts("Test all channels", include_sms=True)
        
        assert 'discord' in results
        assert 'slack' in results  
        assert 'sms' in results
        assert all(results.values())  # All should be True in mock mode


class TestStandaloneFunctions:
    """Test the standalone alert functions for workflow compatibility."""
    
    @patch.dict(os.environ, {
        'GOOGLE_SA_JSON': 'test-json', 
        'TESTING': 'true',
        'TWILIO_SID': '',
        'TWILIO_AUTH': ''
    }, clear=True)
    def test_send_sms_standalone(self):
        """Test standalone send_sms function."""
        result = send_sms("Test standalone SMS")
        assert result is True
    
    @patch.dict(os.environ, {
        'GOOGLE_SA_JSON': 'test-json',
        'TESTING': 'true',
        'DISCORD_WEBHOOK_URL': 'https://discord.com/test-webhook'
    })
    @patch('requests.post')
    def test_send_discord_alert_standalone(self, mock_post):
        """Test standalone send_discord_alert function."""
        mock_post.return_value.status_code = 204
        
        result = send_discord_alert("Test standalone Discord")
        assert result is True
        mock_post.assert_called_once()
    
    @patch.dict(os.environ, {
        'GOOGLE_SA_JSON': 'test-json',
        'TESTING': 'true',
        'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/test-webhook'
    })
    @patch('requests.post')
    def test_send_slack_alert_standalone(self, mock_post):
        """Test standalone send_slack_alert function."""
        mock_post.return_value.status_code = 200
        
        result = send_slack_alert("Test standalone Slack")
        assert result is True
        mock_post.assert_called_once()
    
    @patch.dict(os.environ, {'GOOGLE_SA_JSON': 'test-json', 'TESTING': 'true'})
    def test_singleton_pattern(self):
        """Test that standalone functions use singleton pattern."""
        # Import the private function
        from alerts.notifier import _get_notifier
        
        # Get notifier twice  
        notifier1 = _get_notifier()
        notifier2 = _get_notifier()
        
        # Should be the same instance
        assert notifier1 is notifier2


class TestSecretManagement:
    """Test the get_secret function."""
    
    def test_get_secret_with_env_var(self):
        """Test getting secret from environment."""
        with patch.dict(os.environ, {'TEST_SECRET': 'real-value'}):
            value = get_secret('TEST_SECRET', 'default')
            assert value == 'real-value'
    
    def test_get_secret_with_default(self):
        """Test getting secret with default value."""
        # Make sure TEST_SECRET is not in environment
        with patch.dict(os.environ, {}, clear=True):
            value = get_secret('TEST_SECRET', 'default-value')
            assert value == 'default-value'
    
    def test_get_secret_mock_value(self):
        """Test that mock values are detected."""
        value = get_secret('MISSING_SECRET', 'mock-value')
        assert value == 'mock-value'


class TestErrorHandling:
    """Test error handling in alert functions."""
    
    @patch.dict(os.environ, {
        'GOOGLE_SA_JSON': 'test-json',
        'TESTING': 'true',
        'DISCORD_WEBHOOK_URL': 'https://discord.com/webhook'
    })
    @patch('requests.post')
    def test_discord_network_error(self, mock_post):
        """Test Discord alert handles network errors gracefully."""
        mock_post.side_effect = Exception("Network error")
        
        notifier = AlertNotifier()
        result = notifier.send_discord_alert("Test message")
        
        assert result is False  # Should return False on error
    
    @patch.dict(os.environ, {
        'GOOGLE_SA_JSON': 'test-json',
        'TESTING': 'true',
        'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/webhook'
    })
    @patch('requests.post')
    def test_slack_http_error(self, mock_post):
        """Test Slack alert handles HTTP errors gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("HTTP 500")
        mock_post.return_value = mock_response
        
        notifier = AlertNotifier()
        result = notifier.send_slack_alert("Test message")
        
        assert result is False  # Should return False on error
