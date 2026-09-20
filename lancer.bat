@echo off
REM Lanceur Cave - Windows.   Usage :  lancer bouteille ^| accord ^| appli
setlocal enabledelayedexpansion
set ICI=%~dp0

where py >nul 2>nul
if !errorlevel!==0 (
  py "%ICI%cave.py" %*
  exit /b !errorlevel!
)

where python >nul 2>nul
if !errorlevel!==0 (
  python "%ICI%cave.py" %*
  exit /b !errorlevel!
)

echo.
echo  Python introuvable.
echo  Installe Python depuis https://www.python.org/downloads/
echo  et coche "Add python.exe to PATH" sur le premier ecran.
exit /b 1
