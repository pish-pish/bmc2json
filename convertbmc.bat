@echo off

py "%~dp0bmc.py" --input "%~1" --output "%~n1.json" --tojson 1

if %ERRORLEVEL% NEQ 0 pause