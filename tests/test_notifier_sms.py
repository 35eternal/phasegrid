import os
import unittest
from unittest.mock import patch, MagicMock
from alerts.notifier import send_sms, TwilioNotifier


class TestSMSNotifier(unittest.TestCase):
    """Test SMS notification functionality with Twilio test mode."""

    def setUp(self):
        """Set up test environment variables."""
        self.test_env = {
            'TWILIO_SID': 'ACtest_sid_12345',
            'TWILIO_AUTH': 'test_auth_token',
            'TWILIO_FROM': '+15005550006',  # Twilio test number
            'PHONE_TO': '+15005551234'      # Twilio test recipient
        }
        
    @patch.dict(os.environ, {
        'TWILIO_SID': 'ACtest_sid_12345',
        'TWILIO_AUTH': 'test_auth_token',
        'TWILIO_FROM': '+15005550006',
        'PHONE_TO': '+15005551234'
    })
    @patch('alerts.notifier.Client')
    def test_send_sms_success(self, mock_client_class):
        """Test successful SMS send with mocked Twilio client."""
        # Mock Twilio client and message creation
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_message = MagicMock()
        mock_message.sid = 'SM1234567890abcdef'
        mock_client.messages.create.return_value = mock_message
        
        # Reinitialize notifier with test environment
        with patch('alerts.notifier.TWILIO_ENABLED', True):
            with patch('alerts.notifier._notifier', None):
                result = send_sms("Test alert: PhaseGrid nightly run complete")
        
        # Verify successful return
        self.assertTrue(result)
        
    @patch.dict(os.environ, {})
    @patch('alerts.notifier.TWILIO_ENABLED', False)
    def test_send_sms_missing_credentials(self):
        """Test SMS send fails gracefully when credentials are missing."""
        with patch('alerts.notifier._notifier', None):
            result = send_sms("Test message")
        self.assertFalse(result)
        
    @patch.dict(os.environ, {
        'TWILIO_SID': 'ACtest_sid_12345',
        'TWILIO_AUTH': 'test_auth_token',
        'TWILIO_FROM': '+15005550006',
        'PHONE_TO': '+15005551234'
    })
    @patch('alerts.notifier.Client')
    def test_send_sms_twilio_error(self, mock_client_class):
        """Test SMS send handles Twilio API errors gracefully."""
        # Mock Twilio client to raise exception
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("Twilio API Error")
        
        # Test should not raise, but return False
        with patch('alerts.notifier.TWILIO_ENABLED', True):
            with patch('alerts.notifier._notifier', None):
                result = send_sms("Test alert")
        self.assertFalse(result)
        
    def test_phone_to_env_var(self):
        """Test that PHONE_TO environment variable is used when no number provided."""
        with patch.dict(os.environ, {'PHONE_TO': '+15005551234'}):
            # The function should use PHONE_TO when to_number is None
            with patch('alerts.notifier.TwilioNotifier') as mock_notifier_class:
                mock_instance = MagicMock()
                mock_instance.send_sms.return_value = True
                mock_notifier_class.return_value = mock_instance
                
                with patch('alerts.notifier._notifier', mock_instance):
                    result = send_sms("Test message")
                    
                # Verify the call used the PHONE_TO number
                mock_instance.send_sms.assert_called_with('+15005551234', '[PhaseGrid] Test message')


if __name__ == '__main__':
    unittest.main()
