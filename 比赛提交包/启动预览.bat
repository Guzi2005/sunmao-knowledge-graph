@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  Sunmao Knowledge Graph - local preview
echo  Starting http://127.0.0.1:8080/
echo  Close this window to stop the server.
echo.
where py >nul 2>nul
if %ERRORLEVEL%==0 (set PY=py) else (set PY=python)
start "" http://127.0.0.1:8080/
%PY% -c "import http.server,socketserver; h=socketserver.TCPServer(('127.0.0.1',8080), http.server.SimpleHTTPRequestHandler); print('serving http://127.0.0.1:8080/'); h.serve_forever()"
pause
