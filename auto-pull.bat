@echo off
cd /d "C:\00-KHEPRI"
git add .
git commit -m "Sync automatique %date% %time%"
git pull
git push