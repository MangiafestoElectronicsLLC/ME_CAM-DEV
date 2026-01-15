@echo off
REM Add ME_CAM.com to Windows Hosts File
REM Right-click and select "Run as Administrator"

setlocal enabledelayedexpansion
set "HOSTS_FILE=%WINDIR%\System32\drivers\etc\hosts"

echo.
echo Adding ME_CAM.com to hosts file...
echo.

REM Check if already exists
findstr /C:"ME_CAM.com" "%HOSTS_FILE%" >nul 2>&1
if !errorlevel! equ 0 (
    echo ME_CAM.com is already in your hosts file
    goto :end
)

REM Add to hosts file
echo 10.2.1.47   ME_CAM.com>> "%HOSTS_FILE%"

if !errorlevel! equ 0 (
    echo.
    echo SUCCESS! Added ME_CAM.com to hosts file
    echo.
    echo You can now access: https://ME_CAM.com:8080
    echo.
    echo Note: Ignore the security warning - it's a self-signed certificate
    echo Click "Advanced" then "Proceed" to continue
    echo.
) else (
    echo.
    echo ERROR: Could not write to hosts file
    echo Please run this script as Administrator
    echo.
)

:end
echo.
pause
