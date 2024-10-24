@echo off
echo Installation des dépendances pour le bot Discord...
echo Assurez-vous d'avoir Python et pip installés.

:: Installer discord.py
pip install -U discord.py

:: Installer d'autres dépendances si nécessaire
echo Installation des autres dépendances...
pip install -U asyncio

echo Installation terminée.
pause
