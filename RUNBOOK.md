# PhaseGrid Operations Runbook

## Table of Contents
1. [Overview](#overview)
2. [Multi-Day Dry Run](#multi-day-dry-run)
3. [Guard Rails](#guard-rails)
4. [Guard-Rail Mechanism](#guard-rail-mechanism)
5. [Confidence Threshold Tuning](#confidence-threshold-tuning)
6. [Verify Sheets Status](#verify-sheets-status)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

## Overview

PhaseGrid is an automated sports betting analysis system that generates paper trading slips based on statistical models and real-time odds data.

### Key Components
- **auto_paper.py**: Main script for generating betting slips
- **alert_system.py**: Handles SMS, Discord, and Slack notifications
- **slips_generator.py**: Interfaces with PrizePicks API
- **Database**: SQLite database storing slip history and metrics

## Multi-Day Dry Run

### Running a Multi-Day Dry Run

The enhanced auto_paper.py script now supports multi-day dry runs with state persistence and automatic resumption.

#### Command Line Options

```bash
python auto_paper.py [OPTIONS]
```

**Options:**
- `--start-date YYYY-MM-DD`: Start date for the dry run (default: today)
- `--end-date YYYY-MM-DD`: End date for the dry run (default: today)
- `--sheet-id ID`: Google Sheet ID (default: from GOOGLE_SHEET_ID env)
- `--dry-run`: Run in dry-run mode (default: True)
- `--production`: Run in production mode (disables dry-run)
- `--timezone TZ`: Timezone override (e.g., America/New_York, default: UTC)
- `--min-slips N`: Minimum slips required per day (default: 5)
- `--no-resume`: Do not resume from saved state

#### Examples

**Single day run (today):**
```bash
python auto_paper.py
```

**Multi-day dry run (June 26 - July 5, 2025):**
```bash
python auto_paper.py --start-date 2025-06-26 --end-date 2025-07-05
```

**Resume interrupted run:**
```bash
# If the run was interrupted, just run the same command again
python auto_paper.py --start-date 2025-06-26 --end-date 2025-07-05
# It will automatically skip completed dates
```

**Run with custom timezone:**
```bash
python auto_paper.py --start-date 2025-06-26 --end-date 2025-07-05 --timezone America/New_York
```

**Bypass guard rails for testing:**
```bash
```

### State Persistence

The system automatically saves progress after each day in:
```
data/run_states/dry_run_STARTDATE_to_ENDDATE.json
```

State file contains:
- `completed_dates`: List of successfully processed dates
- `total_slips_generated`: Running total of slips
- `errors`: Any errors encountered
- `last_run`: Timestamp of last update

### Date Handling & Timezones

- Default timezone is **UTC**
- All date boundaries are at 00:00 in the specified timezone
- Use `--timezone` to override (e.g., `America/New_York`, `Europe/London`)
- Dates in logs and filenames use the format `YYYYMMDD`

## Guard Rails

### Minimum Slip Count Protection

The system includes a guard rail that checks if enough slips were generated each day.

**Default behavior:**
- Minimum required slips: 5 per day
- If fewer slips are generated, a **CRITICAL ALERT** is triggered
- Alerts are sent via SMS, Discord, and Slack

**Configuration:**
```bash
# Set custom minimum
python auto_paper.py --min-slips 10

```

### Alert Channels

Critical alerts are sent through:
1. **SMS** (via Twilio): To all numbers in PHONE_TO
2. **Discord**: With @everyone mention
3. **Slack**: With @channel mention

## Guard-Rail Mechanism

### Overview
The slip generation pipeline now includes a guard-rail mechanism to ensure a minimum viable number of slips are generated before proceeding with downstream processes.

### Behavior
- **Default**: Requires minimum of 5 slips to be generated
- **Location**: Implemented in `SlipProcessor.process()`
- **Exception**: Raises `InsufficientSlipsError` when threshold not met
- **Impact**: Prevents empty or low-quality slip sets from propagating

### Bypass Flag
```bash
# Combined with other flags
```

**âš ï¸ Use with caution**: Bypassing the guard-rail may result in insufficient data for meaningful analysis.

## Confidence Threshold Tuning

### Current Settings
- **Primary Threshold**: 0.65 (yielding ~112 slips on WNBA data)
- **Secondary Threshold**: 0.60 (yielding ~43 slips on WNBA data)
- **Location**: Configured in `SlipOptimizer`

### Logging and Analysis
The optimizer now logs detailed rejection reasons:
```
INFO: Rejected slip - Confidence: 0.58 < 0.65 threshold
INFO: Rejected slip - Missing required correlation data
INFO: Accepted slip - Confidence: 0.72, all criteria met
```

### Tuning Guidelines
1. Monitor rejection logs to identify patterns
2. Adjust thresholds based on sport/league characteristics
3. Target 50-150 slips for optimal coverage vs. quality balance
4. Document any threshold changes in commit messages

## Verify Sheets Status

### Current State
- **Status**: Tests unmodified, pending updates
- **Location**: `tests/test_verify_sheets.py`
- **Known Issues**: May require adjustments for new guard-rail logic
- **Priority**: Scheduled for next engineering cycle

### Temporary Workaround
If verify_sheets tests fail due to guard-rail:
2. Or ensure test data generates â‰¥5 slips
3. Document any test modifications in PR

### Quick Reference

#### Daily Workflow
```bash
# Fetch fresh data
python scripts/scraping/fetch_prizepicks_props.py

# Run with guard-rail active (default)
python scripts/auto_paper.py --fetch_lines --days 0

# Check slip count in logs
grep "Generated slips:" logs/auto_paper.log
```

#### Troubleshooting Guard-Rail Issues
- **InsufficientSlipsError**: Check data quality, adjust thresholds, or use bypass flag
- **Low slip counts**: Review rejection logs, consider threshold tuning
- **CI failures**: Verify coverage â‰¥14%, check guard-rail test compatibility

## Monitoring

### New Metrics Tracked

Each slip now includes:
- **confidence_score**: Model confidence (0.0-1.0) based on:
  - Base confidence
  - Edge factor
  - Model variance
  - Historical accuracy
- **closing_line**: Final line value at game time

### Daily Metrics

Daily metrics are saved to:
```
logs/daily_metrics_YYYYMMDD.json
```

Contains:
```json
{
  "date": "2025-06-26",
  "slip_count": 15,
  "average_confidence": 0.725,
  "high_confidence_count": 8,
  "low_confidence_count": 2,
  "timestamp": "2025-06-26T12:00:00Z"
}
```

### Database Schema

The paper_slips table includes these columns:
- `slip_id`: Unique identifier
- `date`: Date of the slip
- `player`: Player name
- `prop_type`: Type of proposition
- `line`: Betting line
- `pick`: over/under selection
- `confidence`: Base model confidence
- **`confidence_score`**: Enhanced confidence score (NEW)
- **`closing_line`**: Final line at game time (NEW)
- `result`: Win/Loss/Push (filled by grader)
- `payout`: Actual payout

## Troubleshooting

### Common Issues

#### 1. Database Migration Errors
```bash
# Run manual migration
python scripts/migrate_schema.py

# Check current schema
python scripts/migrate_schema.py --info

# Dry run to see what would change
python scripts/migrate_schema.py --dry-run
```

#### 2. State File Corruption
```bash
# Remove corrupted state file and restart
rm data/run_states/dry_run_*.json
python auto_paper.py --start-date 2025-06-26 --end-date 2025-07-05 --no-resume
```

#### 3. Guard Rail Triggering
Check:
- PrizePicks API is returning data
- Games are scheduled for the date
- Model is generating predictions

#### 4. Alert Failures
Test alerts:
```python
from alert_system import AlertManager
alert = AlertManager()
alert.test_alerts()
```

### Logs

Check these log locations:
- Main log: `logs/phasegrid.log`
- Daily metrics: `logs/daily_metrics_*.json`
- Workflow artifacts: GitHub Actions artifacts

### Manual Database Queries

```sql
-- Check slip counts by date
SELECT date, COUNT(*) as slip_count 
FROM paper_slips 
GROUP BY date 
ORDER BY date DESC;

-- Check confidence distribution
SELECT 
  date,
  AVG(confidence_score) as avg_confidence,
  COUNT(CASE WHEN confidence_score > 0.7 THEN 1 END) as high_conf,
  COUNT(CASE WHEN confidence_score < 0.3 THEN 1 END) as low_conf
FROM paper_slips
GROUP BY date;

-- Find slips with biggest line movements
SELECT 
  slip_id,
  player,
  prop_type,
  line as original_line,
  closing_line
FROM paper_slips
WHERE closing_line IS NOT NULL
ORDER BY ABS(CAST(line AS FLOAT) - CAST(SUBSTR(closing_line, -5) AS FLOAT)) DESC
LIMIT 10;
```

## Workflow Integration

### GitHub Actions Workflow

The `dryrun.yml` workflow supports:
- **Scheduled runs**: Daily at 7:30 AM ET
- **Manual dispatch**: With date range inputs
- **Automatic runs**: On push/PR to specified branches

Manual trigger via GitHub UI:
1. Go to Actions â†’ Dry Run workflow
2. Click "Run workflow"
3. Enter start/end dates (optional)
4. Check "bypass_guard_rail" if needed

### Environment Variables

Required in GitHub Secrets:
- `GOOGLE_SA_JSON`: Service account JSON
- `GOOGLE_SHEET_ID`: Target spreadsheet ID
- `DISCORD_WEBHOOK_URL`: Discord webhook
- `SLACK_WEBHOOK_URL`: Slack webhook (optional)
- `TWILIO_*`: SMS configuration (optional)

## Best Practices

1. **Always run migration before multi-day runs**
   ```bash
   python scripts/migrate_schema.py
   ```

2. **Monitor daily metrics** for anomalies

3. **Test guard rails** in development:
   ```bash
   python auto_paper.py --min-slips 100 --dry-run
   ```

4. **Use state files** to track long runs

5. **Check timezone settings** for accurate date boundaries

## Emergency Procedures

### If Critical Alert Fires

1. Check logs for specific error
2. Verify PrizePicks API status
3. Check model outputs
4. Manually run for the affected date:
   ```bash
   ```

### If Database Corrupted

1. Stop all running processes
2. Backup current database:
   ```bash
   cp data/paper_metrics.db data/paper_metrics_backup_$(date +%Y%m%d).db
   ```
3. Run migration with fresh schema
4. Restore from CSV backups if needed

### Contact

For urgent issues:
- Check Discord #alerts channel
- Review GitHub Actions logs
- Contact operations team lead
## API Retry and Backoff Behavior

### PrizePicks Scraper Resilience
The PrizePicks scraper (scripts/scraping/fetch_prizepicks_props.py) now includes exponential backoff retry logic:

- **Retry attempts**: 5 times maximum
- **Backoff strategy**: Exponential with multiplier=1, max=30 seconds
- **Total retry time**: Under 30 seconds
- **Error handling**: Logs all attempts and raises after max retries

This prevents transient API failures from breaking the data pipeline.

## CI/CD Coverage Requirements

### Test Coverage Enforcement
The CI pipeline now enforces minimum test coverage:

- **Current threshold**: 34% (configurable via MIN_COVERAGE_THRESHOLD env var)
- **Configuration**: .github/workflows/tests.yml
- **Failure behavior**: CI fails if coverage drops below threshold

## Stats CLI Usage

### Viewing Daily ROI Statistics
The new stats CLI (scripts/stats.py) provides betting performance analytics:

View last 7 days: python scripts/stats.py
View last 30 days: python scripts/stats.py --days 30
Export as HTML: python scripts/stats.py --output html --save-to stats.html
Export as JSON: python scripts/stats.py --output json --save-to stats.json

## Nightly Grader Enhancements

### InsufficientSlipsError Handling
The nightly grader now handles insufficient slip scenarios gracefully:

- **Error class**: InsufficientSlipsError 
- **Logging**: Warnings instead of errors for expected conditions
- **Configurable threshold**: Set MIN_SLIPS_THRESHOLD env var
- **Log retention**: 30 days (increased from 7)
Test Coverage Update (June 2025)
Coverage Achievement
As of June 2025, the project has achieved 15%+ test coverage, meeting the minimum requirements for production deployment.
New Test Files Added

tests/test_small_files.py: Tests for utility scripts and small modules
tests/test_betting_analysis.py: Tests for betting analysis modules
tests/test_check_diagnostic.py: Tests for diagnostic and check scripts
tests/test_coverage_booster.py: Additional tests for configuration and setup modules

CI Coverage Enforcement
The CI pipeline now enforces a minimum coverage of 14% (providing a 1% buffer from our 15% achievement). This ensures code quality doesn't regress below acceptable levels.
Running Tests Locally
bash# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=term

# Run specific test files
pytest tests/test_small_files.py tests/test_betting_analysis.py
Coverage Monitoring
Monitor coverage trends through:

GitHub Actions artifacts (coverage.xml)
Local coverage reports: pytest --cov=. --cov-report=html

## SMS Configuration

### Prerequisites
1. Active Twilio account with SMS-capable phone number
2. GitHub repository admin access to set secrets

### Setup Steps

1. **Obtain Twilio Credentials**
   - Log into Twilio Console (https://console.twilio.com)
   - Copy Account SID from dashboard
   - Generate new Auth Token if needed
   - Note your Twilio phone number (format: +1234567890)

2. **Configure GitHub Secrets**
   Navigate to Settings > Secrets and variables > Actions, then add:
   - TWILIO_SID: Your Account SID
   - TWILIO_AUTH: Your Auth Token
   - TWILIO_FROM: Your Twilio phone number
   - PHONE_TO: Alert recipient phone number
   - SLACK_WEBHOOK_URL: Your Slack webhook URL

3. **Test Configuration**
   Set environment variables locally:
   export TWILIO_SID="your_account_sid"
   export TWILIO_AUTH="your_auth_token"
   export TWILIO_FROM="+1234567890"
   export PHONE_TO="+0987654321"
   
   Run smoke test:
   python scripts/smoke_alert.py --sms

4. **Verify in CI**
   - Trigger manual workflow run with workflow_dispatch
   - Check Actions logs for "SMS alert sent: True"
   - Confirm SMS receipt within 15 seconds

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "SMS disabled - missing credentials" | Verify all 4 secrets are set in GitHub |
| "Twilio error: Invalid phone number" | Ensure E.164 format (+1234567890) |
| "Authentication error" | Regenerate auth token in Twilio console |
| SMS not received | Check Twilio logs, verify phone can receive SMS |

### Cost Management
- SMS alerts trigger on both success and failure
- Monitor usage at console.twilio.com/usage
- Consider using test credentials for development

### Testing with Twilio Test Credentials
For CI/CD testing without charges:
- Use test Account SID: ACtest_sid_12345
- Use magic number: +15005550006 as sender
- Test recipients: +15005551234 (always succeeds)

## Alert Troubleshooting

### Alert Configuration
=======
## Alert Configuration (Discord/Slack)
PhaseGrid uses Discord and Slack for notifications (SMS via Twilio requires 10DLC registration).
### Setting Up Alerts
1. **Discord Webhook**
   - Server Settings â†’ Integrations â†’ Webhooks â†’ New Webhook
   - Add URL to `.env`: `DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...`
2. **Slack Webhook**  
   - Create app at api.slack.com â†’ Incoming Webhooks â†’ Add to Workspace
   - Add URL to `.env`: `SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...`
3. **Test Alerts**
   ```bash
   python -c "from alerts.notifier import send_discord_alert; send_discord_alert('Test')"
   python -c "from alerts.notifier import send_slack_alert; send_slack_alert('Test')"
   ```
### Sheet Health Check
The `sheet-ping` job ensures Google Sheets connectivity after slip generation:
#### How It Works
1. Runs after successful slip generation in `dryrun.yml`
2. Attempts to connect and read from configured sheet
3. Exit codes:
   - `0`: Success - Sheet accessible
   - `1`: General connection failure
   - `2`: Authentication failure (check GOOGLE_SA_JSON)
   - `3`: Sheet not accessible (check SHEET_ID and permissions)
#### Troubleshooting Sheet Ping Failures
1. **Authentication Failed (Exit Code 2)**
   - Verify `GOOGLE_SA_JSON` secret is properly formatted
   - Check service account has not been deleted
   - Ensure JSON is not corrupted during copy/paste
2. **Sheet Not Accessible (Exit Code 3)**
   - Verify `SHEET_ID` matches your Google Sheet
   - Check service account email has Editor access
   - Sheet ID format: Extract from URL `https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit`
3. **Manual Test**
   # Set environment variables
   export SHEET_ID="your-sheet-id"
   export GOOGLE_SA_JSON='{"type": "service_account", ...}'
   # Run ping test
   python scripts/sheet_ping.py
### PrizePicks HTML Fallback
The system now includes automatic HTML fallback for PrizePicks data:
#### When Fallback Activates
1. API returns empty data (`{"data": []}`)
2. API request fails (timeout, 500 error, etc.)
3. API rate limit exceeded
1. Fetches PrizePicks web page for the sport
2. Extracts projection data from embedded JavaScript
3. Falls back to parsing visible HTML cards if needed
4. Returns data in same format as API
#### Testing Fallback
# Test HTML fallback directly
python odds_provider/prizepicks.py --test-html --league NBA
# Force fallback by using wrong API key
PRIZEPICKS_API_KEY="invalid" python odds_provider/prizepicks.py
#### Monitoring Fallback Usage
Check logs for:
- `"Using HTML fallback for NBA projections"` - Fallback activated
- `"Successfully extracted X projections from HTML"` - Fallback succeeded
- `"Both API and HTML methods failed"` - Complete failure

### Alert Thresholds
- Minimum slips required: =5
- Alert channels: Discord, Slack, SMS

