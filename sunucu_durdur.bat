@echo off
taskkill /F /IM python.exe 2>nul
taskkill /F /IM cloudflared.exe 2>nul
echo TSO Sunucusu durduruldu.
pause
