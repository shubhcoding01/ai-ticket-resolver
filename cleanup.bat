@echo off
title Enterprise Windows Cleanup & Maintenance Tool
color 0A

:: ==================================================
:: Enterprise Windows Cleanup & Maintenance Script
:: Compatible with Windows 10 / Windows 11
:: Run as Administrator
:: ==================================================

set LOGFILE=%~dp0CleanupLog_%date:~-4%%date:~4,2%%date:~7,2%.txt

echo =============================================== >> "%LOGFILE%"
echo Windows Cleanup Started - %date% %time% >> "%LOGFILE%"
echo =============================================== >> "%LOGFILE%"

echo.
echo =====================================
echo WINDOWS CLEANUP & MAINTENANCE
echo =====================================
echo.

:: Check Admin Rights
net session >nul 2>&1
if %errorlevel% neq 0 (
echo Please run this script as Administrator.
pause
exit
)

:: --------------------------------------------------
:: Clear User Temp Files
:: --------------------------------------------------
echo Cleaning User Temp Files...
del /f /s /q "%TEMP%*" >nul 2>&1
for /d %%x in ("%TEMP%*") do rd /s /q "%%x" >nul 2>&1

:: --------------------------------------------------
:: Clear Windows Temp
:: --------------------------------------------------
echo Cleaning Windows Temp...
del /f /s /q "C:\Windows\Temp*" >nul 2>&1
for /d %%x in ("C:\Windows\Temp*") do rd /s /q "%%x" >nul 2>&1

:: --------------------------------------------------
:: Empty Recycle Bin
:: --------------------------------------------------
echo Emptying Recycle Bin...
powershell.exe -NoProfile -Command "Clear-RecycleBin -Force" >nul 2>&1

:: --------------------------------------------------
:: Stop Services
:: --------------------------------------------------
echo Stopping Services...
net stop wuauserv >nul 2>&1
net stop bits >nul 2>&1
net stop dosvc >nul 2>&1

:: --------------------------------------------------
:: Clear Windows Update Cache
:: --------------------------------------------------
echo Cleaning Windows Update Cache...
rd /s /q C:\Windows\SoftwareDistribution\Download >nul 2>&1
md C:\Windows\SoftwareDistribution\Download >nul 2>&1

:: --------------------------------------------------
:: DNS Cache Cleanup
:: --------------------------------------------------
echo Flushing DNS Cache...
ipconfig /flushdns

:: --------------------------------------------------
:: Restart Services
:: --------------------------------------------------
echo Starting Services...
net start bits >nul 2>&1
net start wuauserv >nul 2>&1
net start dosvc >nul 2>&1

:: --------------------------------------------------
:: DISM Health Check
:: --------------------------------------------------
echo Running DISM ScanHealth...
DISM /Online /Cleanup-Image /ScanHealth

echo Running DISM RestoreHealth...
DISM /Online /Cleanup-Image /RestoreHealth

:: --------------------------------------------------
:: System File Checker
:: --------------------------------------------------
echo Running SFC Scan...
sfc /scannow

:: --------------------------------------------------
:: Component Store Cleanup
:: --------------------------------------------------
echo Cleaning WinSxS Components...
DISM /Online /Cleanup-Image /StartComponentCleanup

:: --------------------------------------------------
:: Windows Search Rebuild
:: --------------------------------------------------
echo Rebuilding Search Index...
net stop "Windows Search" >nul 2>&1

del /f /q "C:\ProgramData\Microsoft\Search\Data\Applications\Windows\Windows.edb" >nul 2>&1

net start "Windows Search" >nul 2>&1

:: --------------------------------------------------
:: Event Logs Cleanup (Optional)
:: --------------------------------------------------
echo Cleaning Event Logs...
for /F "tokens=*" %%G in ('wevtutil el') do (
wevtutil cl "%%G" >nul 2>&1
)

:: --------------------------------------------------
:: Network Reset
:: --------------------------------------------------
echo Resetting Winsock...
netsh winsock reset >nul 2>&1

echo Resetting TCP/IP...
netsh int ip reset >nul 2>&1

:: --------------------------------------------------
:: Disk Cleanup
:: --------------------------------------------------
echo Running Disk Cleanup...
cleanmgr /verylowdisk

:: --------------------------------------------------
:: Completion
:: --------------------------------------------------
echo.
echo =====================================
echo CLEANUP COMPLETED SUCCESSFULLY
echo =====================================
echo.
echo Recommended: Restart Computer
echo.

echo Completed - %date% %time% >> "%LOGFILE%"
pause
