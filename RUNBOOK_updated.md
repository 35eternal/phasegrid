# PhaseGrid Operations Runbook

## Table of Contents
1. [Overview](#overview)
2. [Multi-Day Dry Run](#multi-day-dry-run)
3. [Guard Rails](#guard-rails)
4. [Monitoring](#monitoring)
5. [Troubleshooting](#troubleshooting)

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