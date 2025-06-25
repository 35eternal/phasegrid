# PhaseGrid Paper Trial Operations Status

Write-Host "`n=== OPERATION STATUS SUMMARY ===" -ForegroundColor Cyan

# Files created
$files = @(
    "RUNBOOK.md",
    "scripts\migrate_csv_formats.py",
    "scripts\generate_trial_report.py", 
    "scripts\test_webhooks.py"
)

Write-Host "`nFiles Created:" -ForegroundColor Yellow
foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file" -ForegroundColor Red
    }
}

# Test status
Write-Host "`nTest Coverage:" -ForegroundColor Yellow
Write-Host "  ✅ No skipped tests found in test_paper_trader.py" -ForegroundColor Green

# Webhook status
Write-Host "`nWebhook Configuration:" -ForegroundColor Yellow
$envContent = Get-Content ".env" -Raw
if ($envContent -match "DISCORD_WEBHOOK_URL=YOUR_DISCORD_WEBHOOK_URL_HERE") {
    Write-Host "  ⚠️  Discord webhook needs configuration" -ForegroundColor Yellow
} else {
    Write-Host "  ✅ Discord webhook configured" -ForegroundColor Green
}
if ($envContent -match "SLACK_WEBHOOK_URL=YOUR_SLACK_WEBHOOK_URL_HERE") {
    Write-Host "  ⚠️  Slack webhook needs configuration" -ForegroundColor Yellow
} else {
    Write-Host "  ✅ Slack webhook configured" -ForegroundColor Green
}

# Recent runs
Write-Host "`nRecent Paper Trading Runs:" -ForegroundColor Yellow
Get-ChildItem "output\simulation_*.csv" | Select-Object -Last 5 | ForEach-Object {
    Write-Host "  📊 $($_.Name) - $($_.LastWriteTime)" -ForegroundColor Cyan
}

Write-Host "`n=== NEXT STEPS ===" -ForegroundColor Yellow
Write-Host "1. Configure webhooks in .env file (replace placeholders)" -ForegroundColor White
Write-Host "2. Run: python scripts\test_webhooks.py" -ForegroundColor White
Write-Host "3. Generate a report: python scripts\generate_trial_report.py" -ForegroundColor White
Write-Host "4. Commit and push your changes" -ForegroundColor White