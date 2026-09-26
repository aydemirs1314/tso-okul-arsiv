@echo off
cd /d "C:\Users\YUSUF AYDEMİR\Desktop\Tso"

:: Django sunucusunu arka planda başlat
start /B "" ".\venv\Scripts\python.exe" manage.py runserver 0.0.0.0:8000

:: Cloudflare tünelini başlat ve log tut
start /B "" "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://127.0.0.1:8000 --logfile "C:\Users\YUSUF AYDEMİR\Desktop\Tso\tunnel_log.txt"
