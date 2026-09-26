@echo off
echo ==========================================
echo   GestureControl AI - Windows Build      
echo ==========================================

echo [1/3] Verifying PyInstaller...
pip install pyinstaller

echo [2/3] Compiling standalone executable...
pyinstaller --noconfirm --onedir --windowed --name "GestureControlAI" --add-data "config.py;." main.py

echo [3/3] Build completed successfully!
echo Executable generated at: dist/GestureControlAI/GestureControlAI.exe
pause
