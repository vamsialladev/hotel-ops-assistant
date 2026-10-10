@echo off
rem Double-click to run the app locally. Runs run_app.ps1 next to this file (no system-wide policy change).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_app.ps1"
