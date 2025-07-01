# PhaseGrid Quick Start Guide

## ?? Getting Started

Welcome to PhaseGrid - an advanced WNBA betting analytics system that leverages player performance cycles, real-time data, and intelligent automation.

### Prerequisites

- Python 3.11+ (Note: You may have issues with numpy on Python 3.13, recommend 3.11)
- Google Cloud account (for Sheets API)
- Discord webhook (for alerts)
- Slack webhook (optional, for team alerts)

### Quick Setup

1. **Clone the repository**
   ```bash
   git clone [your-repo-url]
   cd phasegrid
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Mac/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   copy .env.example .env  # Windows
   # cp .env.example .env  # Mac/Linux
   notepad .env  # Edit with your credentials
   ```

5. **Run your first slip generation**
   ```bash
   python auto_paper.py
   ```

## Daily Dry-Run Automation

The dry-run automation system generates betting slips every morning based on real-time data from PrizePicks and historical performance analysis.

### How It Works

1. **Morning Generation (9 AM Phoenix time)**
   - Fetches current WNBA props from PrizePicks
   - Analyzes player performance cycles
   - Generates confidence-scored betting slips
   - Pushes to Google Sheets with unique IDs

2. **Evening Grading (Midnight Phoenix time)**
   - Fetches game results
   - Grades all pending slips
   - Updates Google Sheets
   - Sends performance summary via Discord/Slack

### Workflow Commands

```bash
# Generate today's slips
python auto_paper.py

# Grade yesterday's slips
python scripts/result_grader.py

# Backfill historical data
python backfill.py --days 7
```

---

## ?? Nightly Grader

The nightly grader is like a robot teacher that grades betting slips while you sleep! Every night at midnight (Phoenix time), it automatically checks yesterday's predictions against the real game results.

### ?? What Does It Do?

Think of it like this:
1. **Fetches Slips** ?? - Gets all the betting predictions from yesterday
2. **Gets Results** ?? - Finds out who actually won the games
3. **Grades** ?? - Marks each prediction as WIN ?, LOSS ?, or PUSH ??
4. **Updates Sheet** ?? - Writes the grades back to Google Sheets
5. **Sends Alerts** ?? - Notifies you via Discord/Slack
6. **Error Handling** ?? - If something breaks, sends emergency alerts

### ? When Does It Run?

The grader runs automatically every night at **midnight Phoenix time**:

- **Winter (MST)**: 12:00 AM MST = 7:00 AM UTC
- **Summer (MDT)**: 12:00 AM MDT = 6:00 AM UTC

Currently set for summer time (MDT): `0 6 * * *` in cron format

**What's cron format?** It's a special way to tell computers when to do things:
```
0 6 * * *
¦ ¦ ¦ ¦ ¦
¦ ¦ ¦ ¦ +--- Day of week (0-7, * means every day)
¦ ¦ ¦ +----- Month (1-12, * means every month)
¦ ¦ +------- Day of month (1-31, * means every day)
¦ +--------- Hour (0-23, 6 means 6 AM UTC)
+----------- Minute (0-59, 0 means exactly on the hour)
```

### ?? Required Secrets (GitHub Settings)

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
| `SHEET_ID` | Your Google Sheet's ID number | Look at your sheet's URL: `https://docs.google.com/spreadsheets/d/`**`1ABC123XYZ`**`/edit` | `1ABC123XYZ` |
| `GOOGLE_SA_JSON` | Google service account login info | Download from Google Cloud Console (JSON file) | `{"type": "service_account", "project_id": "your-project", ...}` |
| `DISCORD_WEBHOOK_URL` | Discord alert URL | From Discord server settings | `https://discord.com/api/webhooks/123/abc...` |
| `SLACK_WEBHOOK_URL` | Slack alert URL (optional) | From Slack app settings | `https://hooks.slack.com/services/123/456/abc...` |
| `RESULTS_API_URL` | Where to get game results | From your sports data provider | `https://api.sportsdata.com/results` |

### ?? Local Development Setup

Want to test on your own computer? Here's how:

#### 1. Create Your Environment File
```bash
# Copy the example file
copy .env.example .env  # Windows
# cp .env.example .env  # Mac/Linux

# Open .env in your text editor and fill in these values:
```

Then add these lines to your `.env` file:
```bash
# Google Sheets
SHEET_ID=your-sheet-id-here
GOOGLE_SA_JSON={"type": "service_account", ...your-full-json-here...}

# Discord (required for alerts)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-here

# Slack (optional team alerts)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your-webhook-here

# Sports API
RESULTS_API_URL=https://api.example.com/results

# Bankroll Configuration
BANKROLL=1000  # Your starting bankroll

# PrizePicks Configuration
PRIZEPICKS_API_KEY=your_prizepicks_api_key_if_available

# Betting Configuration
MIN_CONFIDENCE=0.65
MAX_SLIPS_PER_DAY=10
MIN_BET_PERCENT=0.01
MAX_BET_PERCENT=0.05
KELLY_FRACTION=0.25
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

### ?? Manual Trigger (Run It Yourself)

Sometimes you want to run the grader right now instead of waiting for midnight:

1. Go to your GitHub repository
2. Click the "Actions" tab (top of the page)
3. Click "Nightly Grader" in the left sidebar
4. Click "Run workflow" button (on the right)
5. (Optional) Check "Enable debug logging" for more details
6. Click the green "Run workflow" button
7. Watch it run! (refresh the page after a few seconds)

### ?? What The Alerts Look Like

Every night, you'll get alerts that look like this:

**Discord Message:**
```
?? PhaseGrid Nightly Grader
?? Date: 2024-01-15
?? Total: 25
? Wins: 15
? Losses: 8
?? Errors: 2

?? 2 slips had errors!
```

**Slack Message:**
```
PhaseGrid Bot
? Graded 25 slips successfully
Win Rate: 60% (15W/8L)
Check sheet for details
```

This tells you:
- How many betting slips were graded
- How many were correct predictions (Wins)
- How many were wrong (Losses)
- How many couldn't be graded (Errors)

### ?? Google Sheet Structure

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
| J | `details` | **Added by grader!** Explanation | `? Correct: LAL won (110-105)` |

**Important:** Columns I and J are empty initially - the grader fills them in!

### ?? Troubleshooting Guide

#### Problem: "No alerts received"
**Solutions:**
- ? Check Discord webhook URL is correct in `.env`
- ? Verify Slack webhook URL if using Slack
- ? Make sure webhook URLs start with `https://`
- ? Check GitHub secrets are set correctly (no quotes around values!)
- ? Look at GitHub Actions logs for error messages

#### Problem: "Grading errors"
**Solutions:**
- ? Make sure game IDs in slips match exactly with results API
- ? Check the date format is YYYY-MM-DD everywhere
- ? Verify results API is returning data
- ? Look for typos in team names

#### Problem: "Sheet not updating"
**Solutions:**
- ? Verify Google service account has "Editor" access to your sheet
- ? Check GOOGLE_SA_JSON secret is the complete JSON (copy everything!)
- ? Make sure sheet name is exactly "paper_slips"
- ? Verify columns I and J exist in your sheet

#### Problem: "Workflow not running"
**Solutions:**
- ? Check the workflow file is named exactly `nightly-grader.yml`
- ? Verify it's in `.github/workflows/` folder
- ? Check for typos in the cron schedule
- ? Make sure GitHub Actions is enabled for your repository

#### Problem: "numpy installation failed"
**Solutions:**
- ? Use Python 3.11 instead of 3.13 (numpy may have issues with 3.13)
- ? Install Microsoft C++ Build Tools if on Windows
- ? Try installing numpy separately: `pip install numpy==1.24.3`
- ? Use pre-built wheel: `pip install numpy --only-binary :all:`

### ?? Example Log Output

When the grader runs, you'll see logs like this:

```
==================================================
?? PHASEGRID NIGHTLY GRADER
?? Grading slips from: 2024-01-15
==================================================
Connecting to Google Sheets...
? Connected to Google Sheets!
Setting up alerts...
? Discord webhook configured!
? Slack webhook configured!
?? Looking for slips from 2024-01-15...
?? Found 3 slips for 2024-01-15
?? Fetching game results for 2024-01-15 (using stub data)...
? Got game results!
?? Grading slips...
  Slip slip_001: WIN
  Slip slip_002: LOSS
  Slip slip_003: WIN
?? Writing grades to spreadsheet...
? Updated 3 slip grades
?? Sending Discord alert...
? Discord alert sent!
?? Sending Slack alert...
? Slack alert sent!
==================================================
?? Nightly grader completed successfully!
==================================================
```

---

## ?? Production Hardening Features

### Overview

PhaseGrid has been enhanced with production-ready features to make the system more reliable, scalable, and easier to operate.

### ?? New Features

#### 1. Real Sports Data Integration (PrizePicks + Basketball Reference)

The system now pulls real-time data from:
- **PrizePicks API**: Live player props and betting lines
- **Basketball Reference**: Historical performance data
- **WNBA Stats**: Current season statistics

```python
# Generate real slips with live data
python auto_paper.py

# Slips now include:
# - Real player props from PrizePicks
# - Confidence scores based on historical data
# - Menstrual phase adjustments (if configured)
# - Kelly Criterion bet sizing
```

#### 2. Intelligent Slip ID System

Every slip now has a unique ID format: `PG-{hash}-{date}`
- Prevents duplicate entries
- Enables reliable tracking
- Supports idempotent operations

#### 3. Retry Logic & Error Handling

All external API calls now include:
- Exponential backoff (1s ? 2s ? 4s ? 8s ? 16s)
- Configurable max retries (default: 5)
- Graceful failure handling
- Detailed error logging

#### 4. Discord & Slack Alerts

Get notified about important events:
```python
# Automatic alerts for:
# - Grading complete (with win rate)
# - High confidence opportunities (=85%)
# - Daily/weekly summaries
# - Critical errors

# Manual alerts:
from alerts.notifier import send_discord_alert, send_slack_alert
send_discord_alert("Custom message")
send_slack_alert("Custom message")
```

#### 5. Historical Backfill

Generate slips for past dates:
```bash
# Backfill last 7 days
python backfill.py --days 7

# Force regeneration (ignore existing)
python backfill.py --days 3 --force

# Debug mode for troubleshooting
python backfill.py --days 1 --debug
```

#### 6. Comprehensive Testing

```bash
# Run all tests with coverage
pytest

# Run specific test categories
pytest -m unit          # Fast unit tests
pytest -m integration   # Integration tests
pytest -m "not slow"    # Skip slow tests

# Generate coverage report
pytest --cov-report=html
# Open htmlcov/index.html in browser
```

### ?? Production Features Setup

#### 1. Enhanced Slip Generation
The new `slips_generator.py` replaces the stub with:
- Real PrizePicks data fetching
- Player performance analysis
- Confidence scoring
- Kelly Criterion bet sizing
- Phase-based adjustments

#### 2. Alert System
Configure alerts in `.env`:
- Discord webhooks for all notifications
- Slack webhooks for team collaboration
- Customizable thresholds
- Multiple channel support

#### 3. Backfill Capability
Never miss historical data:
- Generates slips for any date range
- Detects and skips existing slips
- Batch processing for efficiency
- Progress tracking and summaries

### ????? Daily Workflow

#### Morning (Generate Slips)
```bash
# Generate today's slips
python auto_paper.py

# Check high confidence opportunities
# (Automated alerts will be sent if any found)
```

#### Evening (Grade Results)
```bash
# Grade yesterday's slips
python scripts/result_grader.py

# Results automatically pushed to sheet
# Alerts sent with performance summary
```

#### Weekly Maintenance
```bash
# Backfill any missed days
python backfill.py --days 7

# Run tests to ensure everything works
pytest

# Check logs for any issues
type logs\phasegrid.log | findstr ERROR  # Windows
# grep ERROR logs/phasegrid.log          # Mac/Linux
```

### ?? Configuration Options

#### Betting Parameters (.env)
```bash
MIN_CONFIDENCE=0.65      # Only bet on 65%+ confidence
MAX_SLIPS_PER_DAY=10    # Limit daily exposure
MIN_BET_PERCENT=0.01    # Min 1% of bankroll
MAX_BET_PERCENT=0.05    # Max 5% of bankroll
KELLY_FRACTION=0.25     # Conservative Kelly sizing
```

#### Alert Thresholds
- High confidence alerts: Confidence =85%
- Error alerts: Critical errors only
- Daily summaries: Sent at end of grading

### ?? Monitoring & Analytics

#### Check Performance
```python
# View recent results in Google Sheets
# Sheet auto-calculates:
# - Daily/weekly/monthly win rates
# - ROI and profit tracking
# - Best performing prop types
# - Player performance trends
```

#### Debug Issues
```bash
# Check logs
tail -f logs/phasegrid.log  # Real-time log monitoring

# Run in debug mode
LOG_LEVEL=DEBUG python auto_paper.py

# Test specific components
python -m pytest tests/test_slips_generator.py -v
```

### ?? Getting Help

If you're stuck:
1. Check the GitHub Actions logs (Actions tab ? click on the failed run)
2. Look for error messages in red
3. Check all your secrets are set correctly
4. Make sure your `.env` file has all required values (for local testing)
5. Post in Discord with your error message!

### ?? Next Steps

After setting this up:
1. Run it manually first to test (see Manual Trigger section)
2. Check you received the alerts
3. Verify grades appear in columns I and J of your sheet
4. Let it run automatically tonight!
5. Check the results tomorrow morning

Remember: The grader runs at midnight, so tomorrow morning you'll see yesterday's slips graded!

### ?? API Integration

The system now integrates with multiple APIs:

1. **PrizePicks Integration**
   - Fetches live player props
   - Updates throughout the day
   - Handles rate limiting
   - HTML fallback when API fails

2. **Basketball Reference**
   - Historical performance data
   - Season averages
   - Matchup history

3. **Custom Results API**
   - Configure your own endpoint
   - Map to expected format
   - Add authentication as needed

### ?? Future Enhancements

Consider adding these features:
- Support for point spread calculations
- Win/loss streak tracking
- Performance metrics per user
- Weekly/monthly summary reports
- Multiple notification channels (email, Telegram)
- Historical data analysis
- Machine learning predictions
- Multi-sport support
- Live odds tracking
- Arbitrage detection

### ?? Safety Features

1. **Bankroll Protection**
   - Max 5% per bet (configurable)
   - Daily slip limits
   - Automatic stake sizing

2. **Duplicate Prevention**
   - Unique slip IDs
   - Existing slip detection
   - Idempotent operations

3. **Error Recovery**
   - Automatic retries
   - Graceful degradation
   - Detailed error logs

4. **Data Validation**
   - Props verification
   - Line movement detection
   - Odds validation

---

## ?? Dynamic Odds Injector

The Dynamic Odds Injector calculates optimal bet sizes using the Kelly Criterion with phase-based adjustments and bankroll constraints.

### Quick Start

1. **Set Environment Variables**
   ```bash
   export KELLY_FRACTION=0.25      # Fraction of full Kelly (default: 0.25)
   export BANKROLL=1000           # Total bankroll in dollars (default: 1000)
   export MIN_EDGE=0.02           # Minimum edge threshold (default: 0.02)
   export PHASE_CONFIG_PATH=config/phase_config.json  # Phase multipliers config
   ```

2. **Run Manually**
   ```bash
   python scripts/dynamic_odds_injector.py
   ```

3. **Automated Daily Run**
   The injector runs automatically at 12:00 ET daily via GitHub Actions. Check the [Actions tab](../../actions/workflows/dynamic-odds.yml) for run history.

### How It Works

1. **Data Loading**: Reads `predictions_YYYYMMDD.csv` and `data/prizepicks_lines_YYYYMMDD.csv`
2. **Edge Calculation**: Computes edge as `model_probability - implied_probability`
3. **Kelly Sizing**: Applies fractional Kelly formula with phase multipliers
4. **Bankroll Constraint**: Scales down all bets proportionally if total exceeds bankroll
5. **Output**: Generates `bets_YYYYMMDD.csv` with recommended wager sizes

### Example Output

```csv
slip_id,player_name,market,recommended_wager,kelly_percentage,phase_multiplier,edge,win_probability,decimal_odds
SLIP_20250624_0000,LeBron James,points,32.50,0.0325,0.8,0.108,0.65,1.85
SLIP_20250624_0001,Stephen Curry,threes,15.20,0.0190,0.8,0.104,0.58,2.10
```

### Phase Multipliers

The system adjusts bet sizing based on the WNBA season phase:

| Phase | Months | Multiplier | Rationale |
|-------|---------|------------|-----------|
| Preseason | Apr-May 15 | 0.3 | Low confidence in early models |
| Early Season | May 16-31 | 0.5 | Models calibrating |
| Mid Season | Jun-Jul | 0.8 | Stable patterns emerging |
| Late Season | Aug | 1.0 | Full confidence |
| Playoffs | Sep-Oct | 1.2 | High-stakes, proven models |
| Off-Season | Nov-Mar | 0.7 | Default for any off-season activity |

### Testing

Run the test suite:
```bash
pytest tests/test_dynamic_odds.py -v
```

### Monitoring

- **Artifacts**: Each run uploads `bets_YYYYMMDD.csv` as a GitHub artifact
- **Failures**: Automatic issue creation on workflow failures
- **Logs**: Check workflow logs for detailed execution info

### Advanced Configuration

Customize phase multipliers by editing `config/phase_config.json`:
```json
{
  "preseason": 0.3,
  "early_season": 0.5,
  "mid_season": 0.8,
  "late_season": 1.0,
  "playoffs": 1.2,
  "default": 0.7
}
```

### Troubleshooting

1. **No bets generated**: Check if predictions and odds files exist for today
2. **Low wager amounts**: Verify MIN_EDGE isn't too high
3. **Workflow fails**: Check GitHub Issues for automated error reports

---

## ?? Alert Setup

PhaseGrid sends notifications through Discord and Slack when:
- Daily slip generation completes
- Nightly grading runs (success or failure)  
- Errors occur in workflows
- Sheet connectivity issues detected

### Quick Discord Setup (2 minutes)

1. **Create Discord Webhook**
   - Go to your Discord server
   - Server Settings ? Integrations ? Webhooks
   - Click "New Webhook"
   - Name it "PhaseGrid Bot"
   - Choose your alerts channel
   - Copy webhook URL

2. **Add to .env file**
   ```
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/1234567890/abcdefghijk...
   ```

3. **Test It**
   ```bash
   python -c "from alerts.notifier import send_discord_alert; send_discord_alert('PhaseGrid Discord test!')"
   ```

### Quick Slack Setup (3 minutes)

1. **Create Slack App & Webhook**
   - Go to: https://api.slack.com/apps
   - Create app ? From scratch ? Name: "PhaseGrid Bot"
   - Features ? Incoming Webhooks ? ON
   - Add to workspace ? Pick channel
   - Copy webhook URL

2. **Add to .env file**
   ```
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXX
   ```

3. **Test It**
   ```bash
   python -c "from alerts.notifier import send_slack_alert; send_slack_alert('PhaseGrid Slack test!')"
   ```

### Verify Everything Works

Run this command to test all alerts at once:

```bash
# Make sure you've set up .env with your webhooks first
python -c "
from alerts.notifier import send_discord_alert, send_slack_alert
print('Testing Discord...', send_discord_alert('PhaseGrid test - Discord'))  
print('Testing Slack...', send_slack_alert('PhaseGrid test - Slack'))
"
```

You should see:
- `Testing Discord... True` (and a message in Discord!)
- `Testing Slack... True` (and a message in Slack!)

### What Triggers Alerts

- **Success**: "? Graded 15 slips successfully"
- **Failure**: "?? Nightly grading FAILED: [error details]"
- **Sheet Issues**: "? Sheet health check failed"
- **Workflow Links**: Direct links to GitHub Actions logs

### Note on SMS

SMS notifications via Twilio require 10DLC registration (1-3 days) and are not available on trial accounts. Discord and Slack provide instant, free notifications that work just as well!

---

## Paper Trading Trial Mode

The Paper Trading Trial feature simulates betting strategies using historical data and dynamic odds without risking real money. This mode is perfect for testing and refining your betting algorithms.

### Overview

Paper trading allows you to:
- Test betting strategies against historical game results
- Track simulated profit/loss over time
- Analyze strategy performance with detailed metrics
- Run backtests with custom date ranges

### Usage

Run the paper trader with the following command:

```bash
python scripts/paper_trader.py --date YYYYMMDD --results_source stub
```

#### Command Line Arguments

| Argument | Description | Default | Example |
|----------|-------------|---------|---------|
| `--date` | Target date for simulation (YYYYMMDD format) | Required | `20240315` |
| `--results_source` | Data source for game results | `stub` | `stub`, `api`, `csv` |
| `--bankroll` | Starting bankroll amount | `1000.0` | `5000.0` |
| `--bet_size` | Fixed bet size per game | `50.0` | `100.0` |
| `--output_dir` | Directory for output files | `./output` | `./simulations` |

### Output Files

The paper trader generates two output files:

1. **`simulation_YYYYMMDD.csv`** - Detailed bet-by-bet results
   ```csv
   game_id,team,bet_type,odds,bet_amount,win_loss,payout,running_bankroll
   20240315_LA_NY,LA,moneyline,+150,50.0,win,75.0,1075.0
   ```

2. **`daily_summary.json`** - Summary statistics
   ```json
   {
     "date": "20240315",
     "total_bets": 8,
     "wins": 5,
     "losses": 3,
     "win_rate": 0.625,
     "starting_bankroll": 1000.0,
     "ending_bankroll": 1150.0,
     "net_profit": 150.0,
     "roi": 0.15
   }
   ```

### Integration with Dynamic Odds

Paper trading works seamlessly with the Dynamic Odds Injector:

```bash
# Step 1: Generate dynamic odds
python scripts/dynamic_odds_injector.py

# Step 2: Run paper trading simulation
python scripts/paper_trader.py --date 20240315 --results_source stub
```

### Best Practices

- Start with small bet sizes to test strategy viability
- Run simulations across multiple dates to identify patterns
- Monitor the `roi` metric in daily summaries
- Use `--results_source api` for live data testing (requires API key)

## Viewing Performance Statistics

### Using the Stats CLI
After running the system for a few days, view your performance:

View basic stats: python scripts/stats.py
View extended history: python scripts/stats.py --days 30
Generate HTML report: python scripts/stats.py --output html --save-to reports/weekly_stats.html
Export data as JSON: python scripts/stats.py --output json --save-to data/stats_export.json

### System Reliability Features

The system now includes:
- Automatic retry with exponential backoff for API calls
- Test coverage enforcement at 34%
- Enhanced error logging in nightly grader
- Performance statistics tracking
- HTML fallback for PrizePicks when API fails

### Running Tests

The project includes comprehensive test coverage (15%+) to ensure reliability:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=term

# Check if coverage meets minimum (14%)
pytest --cov=. --cov-fail-under=14

# Run specific test categories
pytest tests/test_small_files.py    # Utility module tests
pytest tests/test_betting_analysis.py  # Betting logic tests
pytest tests/test_check_diagnostic.py  # Diagnostic tool tests

# Generate HTML coverage report
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

The CI pipeline automatically runs these tests on every push and pull request, ensuring code quality.

## Alert Testing


## Alert System Configuration

=======
### Discord Alerts
Test Discord functionality after configuring webhook:
```bash
python scripts/smoke_alert.py --discord
```
Expected output:
Testing Discord...
Discord result: True
### Slack Alerts
python scripts/smoke_alert.py --slack
### All Alerts
Test all configured alert channels:
python scripts/smoke_alert.py --discord --slack
---
## ?? Additional Resources
- **GitHub Repository**: [Your repo URL]
- **Google Sheets Template**: [Template URL]
- **Discord Server**: [Invite link]
- **Documentation**: [Wiki or docs URL]
## ?? Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
## ?? License
This project is licensed under the MIT License - see the LICENSE file for details.
## ?? Acknowledgments
- WNBA for providing amazing basketball
- The PhaseGrid team for continuous improvements
- All contributors and testers
**Remember**: Start small, test thoroughly, and scale gradually. Happy betting! ????

## Alert Testing

### SMS Alerts
Test SMS functionality after configuring Twilio credentials:

Basic SMS test:
python scripts/smoke_alert.py --sms

Expected output:
Testing SMS...
SMS result: True

### Slack Alerts
python scripts/smoke_alert.py --slack

### All Alerts
Test all configured alert channels:
python scripts/smoke_alert.py --sms --discord --slack
<<<<<<< HEAD
=======
>>>>>>> origin/main
>>>>>>> feat/alert-finalization
