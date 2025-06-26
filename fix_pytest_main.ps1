# This script removes pytest.main() calls from test files
Write-Host "🔧 Fixing pytest.main() calls in test files..." -ForegroundColor Cyan

$testFiles = @(
    "tests\test_dynamic_odds.py",
    "tests\test_production_hardening.py", 
    "tests\test_repair_sheets.py",
    "tests\test_result_ingestion.py",
    "tests\test_scripts.py"
)

foreach ($file in $testFiles) {
    if (Test-Path $file) {
        Write-Host "  Fixing $file..." -ForegroundColor Yellow
        
        # Read the file
        $content = Get-Content $file -Raw
        
        # Remove the if __name__ == "__main__" block with pytest.main()
        $pattern = '(?ms)^if __name__ == "__main__":\s*\n\s*pytest\.main\([^\)]+\)\s*\n?'
        $newContent = $content -replace $pattern, ''
        
        # Write back to file
        Set-Content -Path $file -Value $newContent -NoNewline
        
        Write-Host "  ✅ Fixed $file" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ File not found: $file" -ForegroundColor Red
    }
}

Write-Host "`n✅ All pytest.main() calls have been removed!" -ForegroundColor Green
