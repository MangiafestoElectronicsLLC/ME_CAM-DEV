@echo off
REM Setup ME_CAM.com domain on Windows
REM Run this as Administrator

echo.
echo Setting up ME_CAM.com domain...
echo.

REM Get Pi IP from user
set /p PI_IP="Enter your Pi's IP address (e.g., 10.2.1.47): "

REM Add to hosts file
echo %PI_IP%  ME_CAM.com >> C:\Windows\System32\drivers\etc\hosts

echo.
echo ✓ Added ME_CAM.com to hosts file
echo.
echo Your Pi IP: %PI_IP%
echo Domain: ME_CAM.com
echo.
echo Next steps:
echo   1. Open browser: https://ME_CAM.com:8080
echo   2. Click "Advanced" → "Proceed" (ignore security warning)
echo   3. Login: admin / admin
echo   4. Change password in Settings
echo.
pause
