@echo off
echo Compiling editor_supportGameList.py to EXE...
pyinstaller --noconfirm editor_supportGameList.spec
echo.
echo Build complete. Results are in the 'dist' folder.
pause
