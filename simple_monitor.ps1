$count = 0
while ($true) {
    $count++
    Write-Host "`r🔄 Check #$count at $(Get-Date -Format 'HH:mm:ss')" -NoNewline
    Start-Sleep -Seconds 30
}
