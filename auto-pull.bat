@echo off
cd /d "C:\00-KHEPRI\khepri"
git add .
git commit -m "Sync automatique %date% %time%"
git pull
git push