# PhaseGrid Quick Start Guide

[Previous sections remain unchanged - don't delete anything above this!]

## Daily Dry-Run Automation

[Previous dry-run documentation remains here - don't delete this section!]

---

## 🌙 Nightly Grader

The nightly grader is like a robot teacher that grades betting slips while you sleep! Every night at midnight (Phoenix time), it automatically checks yesterday's predictions against the real game results.

### 🎯 What Does It Do?

Think of it like this:
1. **Fetches Slips** 📋 - Gets all the betting predictions from yesterday
2. **Gets Results** 🏀 - Finds out who actually won the games
3. **Grades** ✍️ - Marks each prediction as WIN ✅, LOSS ❌, or PUSH 🤝
4. **Updates Sheet** 📊 - Writes the grades back to Google Sheets
5. **Sends Text** 📱 - Texts you a summary of how everyone did
6. **Alerts** 🚨 - If something breaks, sends emergency alerts to Discord

### ⏰ When Does It Run?

The grader runs automatically every night at **midnight Phoenix time**:

- **Winter (MST)**: 12:00 AM MST = 7:00 AM UTC
- **Summer (MDT)**: 12:00 AM MDT = 6:00 AM UTC

Currently set for summer time (MDT): `0 6 * * *` in cron format

**What's cron format?** It's a special way to tell computers when to do things:
```
0 6 * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, * means every day)
│ │ │ └───── Month (1-12, * means every month)
│ │ └─────── Day of month (1-31, * means every day)
│ └───────── Hour (0-23, 6 means 6 AM UTC)
└─────────── Minute (0-59, 0 means exactly on the hour)
```

### 🔐 Required Secrets (GitHub Settings)

These are like passwords that GitHub needs to know. You must set these up in your repository:

**How to add secrets:**
1. Go to your GitHub repository
2. Click "Settings" (it's in the top menu)
3. Click "Secrets and variables" in the left menu
4. Click "Actions"
5. Click "New repository secret" button
6. Add each secret below:

| Secret Name | What Is It? | Where To Get It | Example |
|-------------|-------------|-----------------|---------|
| `GSHEET_ID` | Your Google Sheet's ID number | Look at your sheet's URL: `https://docs.google.com/spreadsheets/d/`**`1ABC123XYZ`**`/edit` | `1ABC123XYZ` |
| `GOOGLE_CREDENTIALS` | Google service account login info | Download from Google Cloud Console (JSON file) | `{"type": "service_account", "project_id": "your-project", ...}` |
| `TWILIO_SID` | Twilio account ID | From twilio.com dashboard | `ACa1b2c3d4e5f6...` |
| `TWILIO_AUTH` | Twilio password | From twilio.com dashboard | `abc123def456...` |
| `TWILIO_FROM` | Your Twilio phone number | From twilio.com (must include +1) | `+14155551234` |
| `PHONE_TO` | Phone to send texts to | Your phone (must include +1) | `+14155555678` |
| `DISCORD_WEBHOOK_URL` | Discord alert URL | From Discord server settings | `https://discord.com/api/webhooks/123/abc...` |
| `RESULTS_API_URL` | Where to get game results | From your sports data provider | `https://api.sportsdata.com/results` |

### 🏠 Local Development Setup

Want to test on your own computer? Here's how:

#### 1. Create Your Environment File
```bash
# Copy the example file
cp .env.example .env

# Open .env in your text editor and fill in these values:
```

Then add these lines to your `.env` file:
```bash
# Google Sheets
GSHEET_ID=your-sheet-id-here

# Twilio (for text messages)
TWILIO_SID=your-twilio-sid-here
TWILIO_AUTH=your-twilio-auth-token-here
TWILIO_FROM=+14155551234  # Your Twilio phone number
PHONE_TO=+14155555678     # Your personal phone number

# Discord (for alerts)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-here

# Sports API
RESULTS_API_URL=https://api.example.com/results
```

#### 2. Install Python Packages
```bash
# Make sure you have Python 3.11 installed
python --version  # Should show "Python 3.11.x"

# Install all required packages
pip install -r requirements.txt
```

#### 3. Run the Grader
```bash
# Run it manually
python scripts/result_grader.py
```

### 🎮 Manual Trigger (Run It Yourself)

Sometimes you want to run the grader right now instead of waiting for midnight:

1. Go to your GitHub repository
2. Click the "Actions" tab (top of the page)
3. Click "Nightly Grader" in the left sidebar
4. Click "Run workflow" button (on the right)
5. (Optional) Check "Enable debug logging" for more details
6. Click the green "Run workflow" button
7. Watch it run! (refresh the page after a few seconds)

### 📱 What The Text Message Looks Like

Every night, you'll get a text that looks like this:

```
🤖 PhaseGrid Nightly Grader Summary
📅 Date: 2024-01-15
📊 Total Slips: 25
✅ Wins: 15
❌ Losses: 8
⚠️ Errors: 2

🚨 WARNING: 2 slips had grading errors!
```

This tells you:
- How many betting slips were graded
- How many were correct predictions (Wins)
- How many were wrong (Losses)
- How many couldn't be graded (Errors)

### 📊 Google Sheet Structure

The grader expects your `paper_slips` sheet to have these columns:

| Column Letter | Column Name | What Goes Here | Example |
|---------------|-------------|----------------|---------|
| A | `id` | Unique ID for each slip | `slip_001` |
| B | `date` | Date of the slip | `2024-01-15` |
| C | `game_id` | Which game this is | `LAL_vs_BOS` |
| D | `pick` | Team they picked to win | `LAL` |
| E | `spread` | Point spread | `-3.5` |
| F | `odds` | Betting odds | `-110` |
| G | `amount` | How much they bet | `$50` |
| H | `timestamp` | When they made the bet | `2024-01-15 10:30:00` |
| I | `grade` | **Added by grader!** WIN/LOSS/PUSH | `WIN` |
| J | `details` | **Added by grader!** Explanation | `✅ Correct! Picked LAL and they won (110-105)` |

**Important:** Columns I and J are empty initially - the grader fills them in!

### 🔧 Troubleshooting Guide

#### Problem: "No SMS received"
**Solutions:**
- ✅ Check Twilio account has money (they charge per text)
- ✅ Verify phone numbers include country code (+1 for USA)
- ✅ Make sure TWILIO_FROM is your Twilio number, not your personal number
- ✅ Check GitHub secrets are set correctly (no quotes around values!)
- ✅ Look at GitHub Actions logs for error messages

#### Problem: "Grading errors"
**Solutions:**
- ✅ Make sure game IDs in slips match exactly with results API
- ✅ Check the date format is YYYY-MM-DD everywhere
- ✅ Verify results API is returning data
- ✅ Look for typos in team names

#### Problem: "Sheet not updating"
**Solutions:**
- ✅ Verify Google service account has "Editor" access to your sheet
- ✅ Check GOOGLE_CREDENTIALS secret is the complete JSON (copy everything!)
- ✅ Make sure sheet name is exactly "paper_slips"
- ✅ Verify columns I and J exist in your sheet

#### Problem: "Workflow not running"
**Solutions:**
- ✅ Check the workflow file is named exactly `nightly-grader.yml`
- ✅ Verify it's in `.github/workflows/` folder
- ✅ Check for typos in the cron schedule
- ✅ Make sure GitHub Actions is enabled for your repository

### 📝 Example Log Output

When the grader runs, you'll see logs like this:

```
==================================================
PHASEGRID NIGHTLY GRADER
==================================================
🚀 Starting the nightly grader...
📅 Grading slips from: 2024-01-15
Connecting to Google Sheets...
✅ Connected to Google Sheets!
Setting up text messaging...
✅ Text messaging ready!
📋 Looking for guesses from 2024-01-15...
📊 Found 3 guesses from yesterday
🏀 Checking who won the games on 2024-01-15...
✅ Got the game results!
📝 Starting to grade slips...
Graded slip slip_001: WIN
Graded slip slip_002: LOSS
Graded slip slip_003: WIN
✍️ Writing grades to the spreadsheet...
✅ Updated 3 grades in the sheet!
📱 Sending SMS from +14155551234 to +14155555678...
✅ Text sent! Message ID: SM123abc...
🎉 Nightly grader finished successfully!
```

### 🆘 Getting Help

If you're stuck:
1. Check the GitHub Actions logs (Actions tab → click on the failed run)
2. Look for error messages in red
3. Check all your secrets are set correctly
4. Make sure your `.env` file has all required values (for local testing)
5. Ask for help in the team Discord channel!

### 🚀 Next Steps

After setting this up:
1. Run it manually first to test (see Manual Trigger section)
2. Check you received the summary text
3. Verify grades appear in columns I and J of your sheet
4. Let it run automatically tonight!
5. Check the results tomorrow morning

Remember: The grader runs at midnight, so tomorrow morning you'll see yesterday's slips graded!