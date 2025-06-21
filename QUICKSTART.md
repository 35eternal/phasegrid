# QUICKSTART - PhaseGrid Betting System

## Google Sheets Setup

Follow these steps to configure Google Sheets integration for the PhaseGrid betting system:

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Sheets API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click on it and press "Enable"

### 2. Create Service Account Credentials

1. In Google Cloud Console, go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in the service account details:
   - Name: `phasegrid-service`
   - Description: "Service account for PhaseGrid betting system"
4. Click "Create and Continue"
5. Skip the optional permissions (click "Continue")
6. Click "Done"

### 3. Generate and Download Credentials

1. Find your newly created service account in the credentials list
2. Click on the service account email
3. Go to the "Keys" tab
4. Click "Add Key" > "Create new key"
5. Choose "JSON" format
6. Click "Create" - this downloads `credentials.json`
7. Move the downloaded file to your project root directory

### 4. Set Up Your Google Sheet

1. Create a new Google Sheet or use an existing one
2. Share the sheet with your service account:
   - Open your Google Sheet
   - Click "Share" button
   - Copy the service account email (ends with `@...iam.gserviceaccount.com`)
   - Paste it in the sharing field
   - Give it "Editor" permissions
   - Click "Send"

### 5. Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
## Daily Dry-Run Automation

The project includes an automated workflow that generates dry-run betting slips daily and pushes them to a Google Sheet for tracking and analysis.

### Purpose
This scheduled workflow runs every day at 3:00 PM UTC to:
- Generate paper trading slips for the current day
- Mark them as dry-run with a unique batch ID
- Push results to the configured Google Sheet

### Required GitHub Secrets
Configure these in your repository's Settings > Secrets:
- `SHEET_ID`: Your Google Sheet ID
- `GOOGLE_SA_JSON`: Service account JSON credentials for Google Sheets API access

### Required Environment Variables
Add these to your `.env` file:
- `TWILIO_SID`: Twilio account SID
- `TWILIO_AUTH`: Twilio auth token
- `TWILIO_FROM`: Twilio phone number (sender)
- `PHONE_TO`: Recipient phone number for alerts

### Workflow Details
- **File path**: `.github/workflows/dryrun.yml`
- **Schedule**: Daily at 3:00 PM UTC (cron: `0 15 * * *`)
- **Manual trigger**: You can also trigger manually from GitHub Actions tab

### Manual Execution
To run the dry-run generation manually:

    python auto_paper.py

Note: Currently the script generates slips for the current day. The `--days` parameter mentioned in the spec would need to be implemented in `auto_paper.py`.
