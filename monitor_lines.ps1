$lastCheck = 0
Write-Host "🏀 PRIZEPICKS WNBA MONITOR" -ForegroundColor Magenta
Write-Host "Checking every 5 minutes for WNBA lines..." -ForegroundColor Yellow

while ($true) {
    $result = python -c "from odds_provider.prizepicks import PrizePicksClient; c = PrizePicksClient(); p = c.fetch_projections('WNBA', True); print(len(p.get('data', [])))" 2>$null
    
    if ($result -gt 0) {
        Write-Host "`n🚨 LINES DETECTED! $result WNBA projections available!" -ForegroundColor Green
        [System.Media.SystemSounds]::Exclamation.Play()
        break
    } else {
        $lastCheck++
        Write-Host "`r⏰ Check #$lastCheck at $(Get-Date -Format 'HH:mm:ss') - No lines yet..." -NoNewline
    }
    
    Start-Sleep -Seconds 300  # 5 minutes
}
