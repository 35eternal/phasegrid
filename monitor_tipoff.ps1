Write-Host "🏀 PHASEGRID GAME-TIME MONITOR" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host "Tip-off: 7:00 PM ET" -ForegroundColor Yellow
Write-Host "Current Time: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan

while ($true) {
    Clear-Host
    Write-Host "🏀 PHASEGRID GAME-TIME MONITOR" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    Write-Host "Current Time: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Recent Activity:" -ForegroundColor Yellow
    Get-ChildItem "logs" -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 3 | ForEach-Object {
        Write-Host "  📄 $($_.Name) - $(($_.LastWriteTime).ToString('HH:mm:ss'))"
    }
    Start-Sleep -Seconds 30
}
