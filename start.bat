@echo off
cd /d "%~dp0"
set OURA_CLIENT_ID=9bf92c9b-e62b-459c-9be6-edaae6b9b1be
set OURA_CLIENT_SECRET=YOUR_SECRET_HERE
set BASE_URL=http://localhost:8089
set SESSION_LOG_PATH=%USERPROFILE%\.wellbeing-sessions.json
set TOKEN_PATH=%USERPROFILE%\.oura-token.json
echo Starting wellbeing-oura server on http://localhost:8089
echo Visit http://localhost:8089/authorize to connect your Oura account
uv run python server.py --http
