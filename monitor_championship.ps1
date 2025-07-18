Write-Host "🏆 COMMISSIONER'S CUP CHAMPIONSHIP MONITOR" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "Championship Game: July 1, 2025" -ForegroundColor Yellow
Write-Host ""

while ($true) {
    $time = Get-Date -Format 'HH:mm:ss'
    Write-Host "`r⏰ $time - Checking for championship lines..." -NoNewline
    
    # Run a quick check
    $result = python -c "from odds_provider.prizepicks import PrizePicks; pp = PrizePicks(); lines = pp.fetch_projections(league_id=7); print(f'Found {len(lines)} lines')" 2>$null
    
    if ($result -match "Found (\d+) lines" -and [int]$matches[1] -gt 0) {
        Write-Host "`n🚨 CHAMPIONSHIP LINES DETECTED! $($matches[1]) lines available!" -ForegroundColor Green
        break
    }
    
    Start-Sleep -Seconds 60
}
