# PhaseGrid Paper Trading Operations Runbook

## Overview
This runbook provides operational procedures for maintaining and monitoring the PhaseGrid Paper Trading Trial system.

## Daily Operations Checklist

### Morning Verification (Before Market Open)
1. **Check System Health**
   - Verify paper trader is ready: `python scripts/paper_trader.py --check-health`
   - Check for prediction files: `Get-ChildItem data\predictions_*.csv`

2. **Verify Webhook Configuration**
   - Test webhook connectivity: `python scripts/test_webhooks.py`

### Automated Daily Run (2 AM UTC via GitHub Actions)
The system automatically runs via `.github/workflows/paper-trial.yml`

Manual trigger if needed: `python scripts/paper_trader.py --date today`

## Alert Response Procedures

### HIGH ROI Alert (>20%)
1. Verify the calculation in `output/paper_metrics.csv`
2. Check for data anomalies
3. Document in daily log

### LOW ROI Alert (<-20%)
1. Review losing bets in `output/paper_slips_YYYYMMDD.csv`
2. Analyze if strategy adjustments needed
3. Check for systematic issues

## Troubleshooting Guide

### Common Issues

#### Missing Predictions File
**Error**: `FileNotFoundError: predictions_YYYYMMDD.csv not found`

**Solution**:
- Check if predictions exist: `Get-ChildItem data\predictions_*.csv`
- Run with specific date: `python scripts/paper_trader.py --date 2025-06-24`

#### Webhook Failures
**Error**: `Webhook delivery failed`

**Solution**:
1. Verify webhook URLs in `.env`
2. Test webhooks: `python scripts/test_webhooks.py`

#### CSV Format Mismatch
**Error**: `KeyError: 'event_id'`

**Solution**: Run migration script: `python scripts/migrate_csv_formats.py`

## Performance Monitoring

### Daily Metrics Review
- View latest metrics: `Get-Content output\paper_metrics.csv -Tail 20`
- Generate performance summary: `python scripts/generate_trial_report.py --period daily`

### Weekly Report Generation
Run every Monday: `python scripts/generate_trial_report.py --period weekly`

## Data Management

### Archive Old Data (Monthly)
PowerShell commands:
- Create archive: `New-Item -Path "archive\$(Get-Date -Format 'yyyy\\MM')" -ItemType Directory -Force`
- Move old files: `Move-Item -Path "output\paper_slips_202505*.csv" -Destination "archive\2025\05"`

### Backup Metrics
`Copy-Item output\paper_metrics.csv "output\paper_metrics_backup_$(Get-Date -Format 'yyyyMMdd').csv"`

## Configuration Reference

### Environment Variables
- `DISCORD_WEBHOOK_URL`: Discord alert webhook
- `SLACK_WEBHOOK_URL`: Slack alert webhook
- `KELLY_FRACTION`: Kelly criterion fraction (default: 0.20)
- `MAX_BANKROLL_RISK`: Maximum bankroll risk per day (default: 0.10)

### File Locations
- Predictions: `data/predictions_YYYYMMDD.csv`
- Paper Slips: `output/paper_slips_YYYYMMDD.csv`
- Metrics: `output/paper_metrics.csv`
- Logs: `logs/paper_trader_YYYYMMDD.log`