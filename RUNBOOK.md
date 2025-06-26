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
- `--bypass-guard-rail`: Bypass guard rail checks
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
python auto_paper.py --bypass-guard-rail --min-slips 10
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

# Bypass for testing
python auto_paper.py --bypass-guard-rail
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
# Override guard-rail for testing or special scenarios
python scripts/auto_paper.py --bypass-guard-rail

# Combined with other flags
python scripts/auto_paper.py --fetch_lines --days 0 --bypass-guard-rail
```

**⚠️ Use with caution**: Bypassing the guard-rail may result in insufficient data for meaningful analysis.

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
1. Use `--bypass-guard-rail` flag in test fixtures
2. Or ensure test data generates ≥5 slips
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
- **CI failures**: Verify coverage ≥14%, check guard-rail test compatibility

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
1. Go to Actions → Dry Run workflow
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
   python auto_paper.py --start-date YYYY-MM-DD --bypass-guard-rail
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
