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