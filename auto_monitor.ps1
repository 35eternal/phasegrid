$checkInterval = 15  # minutes

Write-Host "🏀 AUTOMATED PRIZEPICKS MONITOR" -ForegroundColor Magenta
Write-Host "===============================" -ForegroundColor Magenta
Write-Host "Checking every $checkInterval minutes until lines appear" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

$checkCount = 0

while ($true) {
    $checkCount++
    $time = Get-Date -Format "h:mm:ss tt"
    
    Write-Host "Check #$checkCount at $time" -ForegroundColor White
    
    # Run the check
    $output = python -c "from slips_generator import PrizePicksClient; c = PrizePicksClient(); p = c.get_projections('WNBA'); print(len(p))" 2>&1
    
    if ($output -match "(\d+)" -and [int]$matches[1] -gt 0) {
        Write-Host "🚨 LINES DETECTED! $($matches[1]) projections available!" -ForegroundColor Green
        [System.Media.SystemSounds]::Exclamation.Play()
        
        # Run auto_paper
        python auto_paper_fixed.py --production --bypass-guard-rail
        break
    } else {
        Write-Host "  No lines yet..." -ForegroundColor Gray
    }
    
    # Check time until tipoff
    $tipoff = Get-Date -Hour 19 -Minute 0
    $timeLeft = $tipoff - (Get-Date)
    
    if ($timeLeft.TotalHours -lt 1) {
        Write-Host "  ⚠️ Less than 1 hour until tipoff!" -ForegroundColor Yellow
        $checkInterval = 5  # Check more frequently
    }
    
    Start-Sleep -Seconds ($checkInterval * 60)
}
