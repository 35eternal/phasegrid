# GitHub Actions Configuration
# This file provides configuration when GitHub Secrets aren't available

# Alert Configuration
DISCORD_WEBHOOK_URL="${DISCORD_WEBHOOK_URL:-mock-discord-webhook}"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-mock-slack-webhook}"

# SMS Configuration (Mock Mode)
TWILIO_SID="${TWILIO_SID:-mock-twilio-sid}"
TWILIO_AUTH="${TWILIO_AUTH:-mock-twilio-auth}"
TWILIO_FROM="${TWILIO_FROM:-+1234567890}"
PHONE_TO="${PHONE_TO:-mock}"

# Google Sheets (Mock Mode)
SHEET_ID="${SHEET_ID:-mock-sheet-id}"
GOOGLE_SA_JSON="${GOOGLE_SA_JSON:-mock}"

# Other
RESULTS_API_URL="${RESULTS_API_URL:-mock-api-url}"
MIN_SLIPS_THRESHOLD=5

echo "Environment configured for GitHub Actions"
echo "Mock mode: ${USE_MOCK_ALERTS:-true}"
