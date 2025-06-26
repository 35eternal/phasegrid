# PhaseGrid Project Analyzer
Write-Host "🔍 PHASEGRID PROJECT ANALYSIS 🔍" -ForegroundColor Magenta
Write-Host "================================" -ForegroundColor Magenta

# Current location
Write-Host "`n📍 Current Location:" -ForegroundColor Yellow
Get-Location

# Python files in project
Write-Host "`n🐍 Python Files Found:" -ForegroundColor Yellow
$pythonFiles = Get-ChildItem -Recurse -Filter "*.py" | Where-Object { $_.FullName -notlike "*\venv\*" -and $_.FullName -notlike "*\.venv\*" -and $_.FullName -notlike "*\env\*" }
$pythonFiles | ForEach-Object { Write-Host "  - $($_.FullName.Replace((Get-Location).Path + '\', ''))" }
Write-Host "Total Python files: $($pythonFiles.Count)" -ForegroundColor Green

# Test files specifically
Write-Host "`n🧪 Test Files:" -ForegroundColor Yellow
$testFiles = $pythonFiles | Where-Object { $_.Name -like "test_*.py" -or $_.Name -like "*_test.py" }
if ($testFiles) {
    $testFiles | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Cyan }
} else {
    Write-Host "  No test files found!" -ForegroundColor Red
}

# Check for key files
Write-Host "`n📄 Key Files Status:" -ForegroundColor Yellow
$keyFiles = @{
    "setup.py" = "Package setup file"
    "pyproject.toml" = "Modern Python project config"
    "requirements.txt" = "Dependencies list"
    "README.md" = "Project documentation"
    "RUNBOOK.md" = "Operational guide"
    "QUICKSTART.md" = "Quick start guide"
    ".github/workflows/ci.yml" = "CI pipeline"
}

foreach ($file in $keyFiles.Keys) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file - $($keyFiles[$file])" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file - $($keyFiles[$file])" -ForegroundColor Red
    }
}

# Directory structure (simplified)
Write-Host "`n📁 Main Directories:" -ForegroundColor Yellow
Get-ChildItem -Directory | Where-Object { $_.Name -notmatch "venv|\.venv|env|__pycache__|\..*" } | ForEach-Object {
    Write-Host "  📁 $($_.Name)/" -ForegroundColor Cyan
    $subCount = (Get-ChildItem -Path $_.FullName -File -Filter "*.py" -ErrorAction SilentlyContinue).Count
    if ($subCount -gt 0) {
        Write-Host "     └── $subCount Python files" -ForegroundColor Gray
    }
}

Write-Host "`n================================" -ForegroundColor Magenta
Write-Host "Analysis complete! 🎉" -ForegroundColor Green
