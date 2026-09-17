@echo off
echo ========================================
echo  ProjectIQ - Internet Access Tunnel
echo ========================================
echo.
echo Choose how the app is running:
echo   1. Docker production  (port 8000)  ^<- recommended
echo   2. Dev mode           (port 5173)
echo.
set /p MODE="Enter 1 or 2 [default 1]: "
if "%MODE%"=="" set MODE=1

if "%MODE%"=="1" (
    set TUNNEL_PORT=8000
    echo.
    echo Make sure deploy.bat finished successfully first.
) else (
    set TUNNEL_PORT=5173
    echo.
    echo Make sure start-external.bat is running first.
)

echo.
echo Starting public tunnel on port %TUNNEL_PORT%...
echo.

where cloudflared >nul 2>&1
if not errorlevel 1 (
    echo Using Cloudflare Tunnel ^(stable^)...
    echo Your public URL will appear below. Share it with anyone.
    echo Press Ctrl+C to stop the tunnel.
    echo.
    cloudflared tunnel --url http://localhost:%TUNNEL_PORT%
    goto :done
)

echo cloudflared not found. Using localtunnel instead...
echo Install cloudflared for a better experience:
echo   winget install Cloudflare.cloudflared
echo.
npx --yes localtunnel --port %TUNNEL_PORT%

:done
pause
