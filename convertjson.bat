@echo off

py "%~dp0bmc.py" --input "%~1" --output "%~n1.bmc" --tobinary

if %ERRORLEVEL% NEQ 0 pause