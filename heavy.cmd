@echo off
rem Startet Heavy aus diesem Ordner:  heavy.cmd <befehl>
cd /d "%~dp0"
python -m heavy %*
