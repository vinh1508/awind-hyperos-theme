@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (
  py -3 tools\mtz_tool.py build --csv translations.csv --out dist\ViHoa-K80Pro-POC-v0.1.mtz
  py -3 tools\mtz_tool.py inspect dist\ViHoa-K80Pro-POC-v0.1.mtz
) else (
  python tools\mtz_tool.py build --csv translations.csv --out dist\ViHoa-K80Pro-POC-v0.1.mtz
  python tools\mtz_tool.py inspect dist\ViHoa-K80Pro-POC-v0.1.mtz
)
pause
