# Save this entire block as check_paper_status.ps1

Write-Host "`n=== PAPER TRADING OPERATIONS STATUS CHECK ===" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Check if we're on the right branch
$currentBranch = git branch --show-current
Write-Host "`nCurrent Branch: $currentBranch" -ForegroundColor Yellow
if ($currentBranch -eq "chore/paper-trial-operations") {
    Write-Host "✅ On correct branch!" -ForegroundColor Green
} else {
    Write-Host "❌ Not on correct branch (should be chore/paper-trial-operations)" -ForegroundColor Red
}

# Check for paper trader script
Write-Host "`nChecking Paper Trader Script:" -ForegroundColor Yellow
if (Test-Path "scripts\paper_trader.py") {
    Write-Host "✅ scripts\paper_trader.py exists" -ForegroundColor Green
} else {
    Write-Host "❌ scripts\paper_trader.py not found" -ForegroundColor Red
}

# Check for GitHub workflow
Write-Host "`nChecking GitHub Workflow:" -ForegroundColor Yellow
if (Test-Path ".github\workflows\paper-trial.yml") {
    Write-Host "✅ .github\workflows\paper-trial.yml exists" -ForegroundColor Green
} else {
    Write-Host "❌ .github\workflows\paper-trial.yml not found" -ForegroundColor Red
}

# Check for documentation
Write-Host "`nChecking Documentation:" -ForegroundColor Yellow
if (Test-Path "RUNBOOK.md") {
    Write-Host "✅ RUNBOOK.md exists" -ForegroundColor Green
} else {
    Write-Host "❌ RUNBOOK.md not found" -ForegroundColor Red
}

if (Test-Path "QUICKSTART.md") {
    Write-Host "✅ QUICKSTART.md exists" -ForegroundColor Green
} else {
    Write-Host "❌ QUICKSTART.md not found" -ForegroundColor Red
}

# Check for test files
Write-Host "`nChecking Test Files:" -ForegroundColor Yellow
$paperTests = Get-ChildItem -Path "tests" -Filter "*paper*.py" -ErrorAction SilentlyContinue
if ($paperTests) {
    Write-Host "✅ Found paper trading tests:" -ForegroundColor Green
    $paperTests | ForEach-Object { Write-Host "   - $($_.Name)" -ForegroundColor Gray }
} else {
    Write-Host "❌ No paper trading tests found" -ForegroundColor Red
}

# Check for .env file
Write-Host "`nChecking Environment:" -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✅ .env file exists" -ForegroundColor Green
    # Check for webhook placeholders
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "DISCORD_WEBHOOK|SLACK_WEBHOOK") {
        Write-Host "   📌 Found webhook configuration entries" -ForegroundColor Cyan
    }
} else {
    Write-Host "❌ .env file not found" -ForegroundColor Red
}

# Check for output files
Write-Host "`nChecking Output Files:" -ForegroundColor Yellow
if (Test-Path "output\paper_metrics.csv") {
    Write-Host "✅ output\paper_metrics.csv exists" -ForegroundColor Green
} else {
    Write-Host "❌ output\paper_metrics.csv not found" -ForegroundColor Red
}

Write-Host "`n=== STATUS CHECK COMPLETE ===" -ForegroundColor Cyan