# PhaseGrid Quick Start Guide

## ðŸš€ Getting Started

Welcome to PhaseGrid - an advanced WNBA betting analytics system that leverages player performance cycles, real-time data, and intelligent automation.

### Prerequisites

- Python 3.11+ (Note: You may have issues with numpy on Python 3.13, recommend 3.11)
- Google Cloud account (for Sheets API)
- Twilio account (optional, for SMS alerts)
- Discord webhook (optional, for alerts)

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
   - Sends performance summary via SMS/Discord

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

## ðŸŒ™ Nightly Grader

The nightly grader is like a robot teacher that grades betting slips while you sleep! Every night at midnight (Phoenix time), it automatically checks yesterday's predictions against the real game results.

### ðŸŽ¯ What Does It Do?

Think of it like this:
1. **Fetches Slips** ðŸ“‹ - Gets all the betting predictions from yesterday
2. **Gets Results** ðŸ€ - Finds out who actually won the games
3. **Grades** âœï¸ - Marks each prediction as WIN âœ…, LOSS âŒ, or PUSH ðŸ¤
4. **Updates Sheet** ðŸ“Š - Writes the grades back to Google Sheets
5. **Sends Text** ðŸ“± - Texts you a summary of how everyone did
6. **Alerts** ðŸš¨ - If something breaks, sends emergency alerts to Discord

### â° When Does It Run?

The grader runs automatically every night at **midnight Phoenix time**:

- **Winter (MST)**: 12:00 AM MST = 7:00 AM UTC
- **Summer (MDT)**: 12:00 AM MDT = 6:00 AM UTC

Currently set for summer time (MDT): `0 6 * * *` in cron format

**What's cron format?** It's a special way to tell computers when to do things:
```
0 6 * * *
â”‚ â”‚ â”‚ â”‚ â”‚
â”‚ â”‚ â”‚ â”‚ â””â”€â”€â”€ Day of week (0-7, * means every day)
â”‚ â”‚ â”‚ â””â”€â”€â”€â”€â”€ Month (1-12, * means every month)
â”‚ â”‚ â””â”€â”€â”€â”€â”€â”€â”€ Day of month (1-31, * means every day)
â”‚ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€ Hour (0-23, 6 means 6 AM UTC)
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Minute (0-59, 0 means exactly on the hour)
```

### ðŸ” Required Secrets (GitHub Settings)

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
| `TWILIO_SID` | Twilio account ID | From twilio.com dashboard | `ACa1b2c3d4e5f6...` |
| `TWILIO_AUTH` | Twilio password | From twilio.com dashboard | `abc123def456...` |
| `TWILIO_FROM` | Your Twilio phone number | From twilio.com (must include +1) | `+18331234567` |
| `PHONE_TO` | Phone to send texts to | Your phone (must include +1) | `+14805551234` |
| `DISCORD_WEBHOOK_URL` | Discord alert URL | From Discord server settings | `https://discord.com/api/webhooks/123/abc...` |
| `RESULTS_API_URL` | Where to get game results | From your sports data provider | `https://api.sportsdata.com/results` |

### ðŸ  Local Development Setup

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

# Twilio (for text messages)
TWILIO_SID=your-twilio-sid-here
TWILIO_AUTH=your-twilio-auth-token-here
TWILIO_FROM=+18331234567  # Your Twilio phone number
PHONE_TO=+14805551234     # Your personal phone number

# Discord (for alerts)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-here

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

### ðŸŽ® Manual Trigger (Run It Yourself)

Sometimes you want to run the grader right now instead of waiting for midnight:

1. Go to your GitHub repository
2. Click the "Actions" tab (top of the page)
3. Click "Nightly Grader" in the left sidebar
4. Click "Run workflow" button (on the right)
5. (Optional) Check "Enable debug logging" for more details
6. Click the green "Run workflow" button
7. Watch it run! (refresh the page after a few seconds)

### ðŸ“± What The Text Message Looks Like

Every night, you'll get a text that looks like this:

```
ðŸ¤– PhaseGrid Nightly Grader
ðŸ“… Date: 2024-01-15
ðŸ“Š Total: 25
âœ… Wins: 15
âŒ Losses: 8
âš ï¸ Errors: 2

ðŸš¨ 2 slips had errors!
```

This tells you:
- How many betting slips were graded
- How many were correct predictions (Wins)
- How many were wrong (Losses)
- How many couldn't be graded (Errors)

### ðŸ“Š Google Sheet Structure

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
| J | `details` | **Added by grader!** Explanation | `âœ… Correct: LAL won (110-105)` |

**Important:** Columns I and J are empty initially - the grader fills them in!

### ðŸ”§ Troubleshooting Guide

#### Problem: "No SMS received"
**Solutions:**
- âœ… Check Twilio account has money (they charge per text)
- âœ… Verify phone numbers include country code (+1 for USA)
- âœ… Make sure TWILIO_FROM is your Twilio number, not your personal number
- âœ… Check GitHub secrets are set correctly (no quotes around values!)
- âœ… Look at GitHub Actions logs for error messages

#### Problem: "Grading errors"
**Solutions:**
- âœ… Make sure game IDs in slips match exactly with results API
- âœ… Check the date format is YYYY-MM-DD everywhere
- âœ… Verify results API is returning data
- âœ… Look for typos in team names

#### Problem: "Sheet not updating"
**Solutions:**
- âœ… Verify Google service account has "Editor" access to your sheet
- âœ… Check GOOGLE_SA_JSON secret is the complete JSON (copy everything!)
- âœ… Make sure sheet name is exactly "paper_slips"
- âœ… Verify columns I and J exist in your sheet

#### Problem: "Workflow not running"
**Solutions:**
- âœ… Check the workflow file is named exactly `nightly-grader.yml`
- âœ… Verify it's in `.github/workflows/` folder
- âœ… Check for typos in the cron schedule
- âœ… Make sure GitHub Actions is enabled for your repository

#### Problem: "numpy installation failed"
**Solutions:**
- âœ… Use Python 3.11 instead of 3.13 (numpy may have issues with 3.13)
- âœ… Install Microsoft C++ Build Tools if on Windows
- âœ… Try installing numpy separately: `pip install numpy==1.24.3`
- âœ… Use pre-built wheel: `pip install numpy --only-binary :all:`

### ðŸ“ Example Log Output

When the grader runs, you'll see logs like this:

```
==================================================
ðŸš€ PHASEGRID NIGHTLY GRADER
ðŸ“… Grading slips from: 2024-01-15
==================================================
Connecting to Google Sheets...
âœ… Connected to Google Sheets!
Setting up text messaging...
âœ… Text messaging ready!
ðŸ“‹ Looking for slips from 2024-01-15...
ðŸ“Š Found 3 slips for 2024-01-15
ðŸ€ Fetching game results for 2024-01-15 (using stub data)...
âœ… Got game results!
ðŸ“ Grading slips...
  Slip slip_001: WIN
  Slip slip_002: LOSS
  Slip slip_003: WIN
âœï¸ Writing grades to spreadsheet...
âœ… Updated 3 slip grades
ðŸ“± Sending SMS from +18331234567 to +14805551234...
âœ… SMS sent! ID: SM123abc...
==================================================
ðŸŽ‰ Nightly grader completed successfully!
==================================================
```

---

## ðŸš€ Production Hardening Features

### Overview

PhaseGrid has been enhanced with production-ready features to make the system more reliable, scalable, and easier to operate.

### ðŸŽ¯ New Features

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
- Exponential backoff (1s â†’ 2s â†’ 4s â†’ 8s â†’ 16s)
- Configurable max retries (default: 5)
- Graceful failure handling
- Detailed error logging

#### 4. SMS & Discord Alerts

Get notified about important events:
```python
# Automatic alerts for:
# - Grading complete (with win rate)
# - High confidence opportunities (â‰¥85%)
# - Daily/weekly summaries
# - Critical errors

# Manual alerts:
from alerts import send_quick_sms, send_quick_discord
send_quick_sms("Custom message")
send_quick_discord("Custom message", color=0x00FF00)
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

### ðŸ“‹ Production Features Setup

#### 1. Enhanced Slip Generation
The new `slips_generator.py` replaces the stub with:
- Real PrizePicks data fetching
- Player performance analysis
- Confidence scoring
- Kelly Criterion bet sizing
- Phase-based adjustments

#### 2. Alert System
Configure alerts in `.env`:
- SMS via Twilio for critical events
- Discord webhooks for all notifications
- Customizable thresholds
- Multiple recipient support

#### 3. Backfill Capability
Never miss historical data:
- Generates slips for any date range
- Detects and skips existing slips
- Batch processing for efficiency
- Progress tracking and summaries

### ðŸƒâ€â™‚ï¸ Daily Workflow

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

### ðŸ”§ Configuration Options

#### Betting Parameters (.env)
```bash
MIN_CONFIDENCE=0.65      # Only bet on 65%+ confidence
MAX_SLIPS_PER_DAY=10    # Limit daily exposure
MIN_BET_PERCENT=0.01    # Min 1% of bankroll
MAX_BET_PERCENT=0.05    # Max 5% of bankroll
KELLY_FRACTION=0.25     # Conservative Kelly sizing
```

#### Alert Thresholds
- SMS alerts: Win rate â‰¥70% or â‰¤30%, profit Â±$500
- High confidence alerts: Confidence â‰¥85%
- Error alerts: Critical errors only

### ðŸ“Š Monitoring & Analytics

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

### ðŸ†˜ Getting Help

If you're stuck:
1. Check the GitHub Actions logs (Actions tab â†’ click on the failed run)
2. Look for error messages in red
3. Check all your secrets are set correctly
4. Make sure your `.env` file has all required values (for local testing)
5. Ask for help in the team Discord channel!

### ðŸš€ Next Steps

After setting this up:
1. Run it manually first to test (see Manual Trigger section)
2. Check you received the summary text
3. Verify grades appear in columns I and J of your sheet
4. Let it run automatically tonight!
5. Check the results tomorrow morning

Remember: The grader runs at midnight, so tomorrow morning you'll see yesterday's slips graded!

### ðŸ”Œ API Integration

The system now integrates with multiple APIs:

1. **PrizePicks Integration**
   - Fetches live player props
   - Updates throughout the day
   - Handles rate limiting

2. **Basketball Reference**
   - Historical performance data
   - Season averages
   - Matchup history

3. **Custom Results API**
   - Configure your own endpoint
   - Map to expected format
   - Add authentication as needed

### ðŸ“ˆ Future Enhancements

Consider adding these features:
- Support for point spread calculations
- Win/loss streak tracking
- Performance metrics per user
- Weekly/monthly summary reports
- Multiple notification channels (email, Slack)
- Historical data analysis
- Machine learning predictions
- Multi-sport support
- Live odds tracking
- Arbitrage detection

### ðŸš¨ Safety Features

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

## ðŸ’° Dynamic Odds Injector

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

## ðŸ“š Additional Resources

- **GitHub Repository**: [Your repo URL]
- **Google Sheets Template**: [Template URL]
- **Discord Server**: [Invite link]
- **Documentation**: [Wiki or docs URL]

## ðŸ¤ Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## ðŸ“„ License

This project is licensed under the MIT License - see the LICENSE file for details.

## ðŸ™ Acknowledgments

- WNBA for providing amazing basketball
- The PhaseGrid team for continuous improvements
- All contributors and testers

---

**Remember**: Start small, test thoroughly, and scale gradually. Happy betting! ðŸ€ðŸ“Š

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


