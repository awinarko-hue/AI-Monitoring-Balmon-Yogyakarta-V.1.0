@echo off
echo =========================================================
echo  Menjalankan AI Monitoring Balmon Yogyakarta
echo  URL: http://127.0.0.1:3000/
echo =========================================================
cd /d "%~dp0backend"
python run.py --port 3000
pause
