# GestureControl AI - Windows Executable Build Script (PyInstaller)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  GestureControl AI - Windows Build      " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Install Build Dependencies
Write-Host "[1/3] Verifying PyInstaller installation..." -ForegroundColor Yellow
pip install pyinstaller

# 2. Run PyInstaller
Write-Host "[2/3] Compiling standalone executable..." -ForegroundColor Yellow
pyinstaller --noconfirm --onedir --windowed `
    --name "GestureControlAI" `
    --add-data "config.py;." `
    --add-data "settings.json;." `
    main.py

Write-Host "[3/3] Build completed successfully!" -ForegroundColor Green
Write-Host "Executable generated at: dist/GestureControlAI/GestureControlAI.exe" -ForegroundColor Cyan
