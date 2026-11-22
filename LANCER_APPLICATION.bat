@echo off
title ImmoScribe AI - Serveur Local
echo ========================================================
echo        LANCEMENT DE IMMOSCRIBE AI (SAAS IMMOBILIER)
echo ========================================================
echo.
echo Demarrage du serveur local sur http://localhost:5000 ...
set GEMINI_API_KEY=AQ.Ab8RN6LVTjt5uwp0_jdvlzckwpr1xMU577yMTgd1GSusAugzDg
start http://localhost:5000
python server.py
pause
