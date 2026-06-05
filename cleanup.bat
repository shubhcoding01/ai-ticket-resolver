@REM @echo off
@REM title Enterprise Windows Cleanup & Maintenance Tool
@REM color 0A

@REM :: ==================================================
@REM :: Enterprise Windows Cleanup & Maintenance Script
@REM :: Compatible with Windows 10 / Windows 11
@REM :: Run as Administrator
@REM :: ==================================================

@REM set LOGFILE=%~dp0CleanupLog_%date:~-4%%date:~4,2%%date:~7,2%.txt

@REM echo =============================================== >> "%LOGFILE%"
@REM echo Windows Cleanup Started - %date% %time% >> "%LOGFILE%"
@REM echo =============================================== >> "%LOGFILE%"

@REM echo.
@REM echo =====================================
@REM echo WINDOWS CLEANUP & MAINTENANCE
@REM echo =====================================
@REM echo.

@REM :: Check Admin Rights
@REM net session >nul 2>&1
@REM if %errorlevel% neq 0 (
@REM echo Please run this script as Administrator.
@REM pause
@REM exit
@REM )

@REM :: --------------------------------------------------
@REM :: Clear User Temp Files
@REM :: --------------------------------------------------
@REM echo Cleaning User Temp Files...
@REM del /f /s /q "%TEMP%*" >nul 2>&1
@REM for /d %%x in ("%TEMP%*") do rd /s /q "%%x" >nul 2>&1

@REM :: --------------------------------------------------
@REM :: Clear Windows Temp
@REM :: --------------------------------------------------
@REM echo Cleaning Windows Temp...
@REM del /f /s /q "C:\Windows\Temp*" >nul 2>&1
@REM for /d %%x in ("C:\Windows\Temp*") do rd /s /q "%%x" >nul 2>&1

@REM :: --------------------------------------------------
@REM :: Empty Recycle Bin
@REM :: --------------------------------------------------
@REM echo Emptying Recycle Bin...
@REM powershell.exe -NoProfile -Command "Clear-RecycleBin -Force" >nul 2>&1

@REM :: --------------------------------------------------
@REM :: Stop Services
@REM :: --------------------------------------------------
@REM echo Stopping Services...
@REM net stop wuauserv >nul 2>&1
@REM net stop bits >nul 2>&1
@REM net stop dosvc >nul 2>&1

@REM :: --------------------------------------------------
@REM :: Clear Windows Update Cache
@REM :: --------------------------------------------------
@REM echo Cleaning Windows Update Cache...
@REM rd /s /q C:\Windows\SoftwareDistribution\Download >nul 2>&1
@REM md C:\Windows\SoftwareDistribution\Download >nul 2>&1

@REM :: --------------------------------------------------
@REM :: DNS Cache Cleanup
@REM :: --------------------------------------------------
@REM echo Flushing DNS Cache...
@REM ipconfig /flushdns

@REM :: --------------------------------------------------
@REM :: Restart Services
@REM :: --------------------------------------------------
@REM echo Starting Services...
@REM net start bits >nul 2>&1
@REM net start wuauserv >nul 2>&1
@REM net start dosvc >nul 2>&1

@REM :: --------------------------------------------------
@REM :: DISM Health Check
@REM :: --------------------------------------------------
@REM echo Running DISM ScanHealth...
@REM DISM /Online /Cleanup-Image /ScanHealth

@REM echo Running DISM RestoreHealth...
@REM DISM /Online /Cleanup-Image /RestoreHealth

@REM :: --------------------------------------------------
@REM :: System File Checker
@REM :: --------------------------------------------------
@REM echo Running SFC Scan...
@REM sfc /scannow

@REM :: --------------------------------------------------
@REM :: Component Store Cleanup
@REM :: --------------------------------------------------
@REM echo Cleaning WinSxS Components...
@REM DISM /Online /Cleanup-Image /StartComponentCleanup

@REM :: --------------------------------------------------
@REM :: Windows Search Rebuild
@REM :: --------------------------------------------------
@REM echo Rebuilding Search Index...
@REM net stop "Windows Search" >nul 2>&1

@REM del /f /q "C:\ProgramData\Microsoft\Search\Data\Applications\Windows\Windows.edb" >nul 2>&1

@REM net start "Windows Search" >nul 2>&1

@REM :: --------------------------------------------------
@REM :: Event Logs Cleanup (Optional)
@REM :: --------------------------------------------------
@REM echo Cleaning Event Logs...
@REM for /F "tokens=*" %%G in ('wevtutil el') do (
@REM wevtutil cl "%%G" >nul 2>&1
@REM )

@REM :: --------------------------------------------------
@REM :: Network Reset
@REM :: --------------------------------------------------
@REM echo Resetting Winsock...
@REM netsh winsock reset >nul 2>&1

@REM echo Resetting TCP/IP...
@REM netsh int ip reset >nul 2>&1

@REM :: --------------------------------------------------
@REM :: Disk Cleanup
@REM :: --------------------------------------------------
@REM echo Running Disk Cleanup...
@REM cleanmgr /verylowdisk

@REM :: --------------------------------------------------
@REM :: Completion
@REM :: --------------------------------------------------
@REM echo.
@REM echo =====================================
@REM echo CLEANUP COMPLETED SUCCESSFULLY
@REM echo =====================================
@REM echo.
@REM echo Recommended: Restart Computer
@REM echo.

@REM echo Completed - %date% %time% >> "%LOGFILE%"
@REM pause



@echo off
setlocal EnableDelayedExpansion
title Enterprise Windows Cleanup & Maintenance Tool — ICICI Bank IT
color 0A

:: ==================================================
:: Enterprise Windows Cleanup & Maintenance Script
:: ICICI Bank — IT Support Automation
:: Compatible with Windows 10 / Windows 11
:: Must be run as Administrator
:: Version 2.0
:: ==================================================

:: --------------------------------------------------
:: Setup Log File with timestamp
:: --------------------------------------------------
set LOGDIR=%~dp0logs
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

set TIMESTAMP=%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set LOGFILE=%LOGDIR%\CleanupLog_%TIMESTAMP%.txt
set ERRORCOUNT=0
set FREEDSPACE_BEFORE=0
set FREEDSPACE_AFTER=0

call :Log "================================================="
call :Log "ICICI Bank — Windows Cleanup & Maintenance Tool"
call :Log "Started: %date% %time%"
call :Log "Machine: %COMPUTERNAME%"
call :Log "User   : %USERNAME%"
call :Log "================================================="

echo.
echo =====================================================
echo  ICICI BANK — WINDOWS CLEANUP ^& MAINTENANCE TOOL
echo =====================================================
echo  Machine : %COMPUTERNAME%
echo  User    : %USERNAME%
echo  Log     : %LOGFILE%
echo =====================================================
echo.

:: --------------------------------------------------
:: Step 1 — Check Administrator Rights
:: --------------------------------------------------
call :Log "Step 1 — Checking administrator rights..."
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] This script must be run as Administrator.
    echo Right-click the script and choose "Run as administrator"
    call :Log "ERROR: Not running as administrator. Exiting."
    pause
    exit /b 1
)
call :Log "Administrator check PASSED."
echo [OK] Running as Administrator

:: --------------------------------------------------
:: Step 2 — Record Disk Space Before
:: --------------------------------------------------
call :Log "Step 2 — Recording disk space before cleanup..."
for /f "tokens=3" %%a in ('dir C:\ ^| find "bytes free"') do set FREEDSPACE_BEFORE=%%a
call :Log "Disk free before: %FREEDSPACE_BEFORE% bytes"
echo [INFO] Disk space before cleanup recorded.

:: --------------------------------------------------
:: Step 3 — Clear User Temp Files
:: --------------------------------------------------
call :Log "Step 3 — Clearing user temp files..."
echo Cleaning user temp files...
del /f /s /q "%TEMP%\*" >nul 2>&1
for /d %%x in ("%TEMP%\*") do rd /s /q "%%x" >nul 2>&1
call :Log "User temp files cleared."
echo [OK] User temp files cleared.

:: --------------------------------------------------
:: Step 4 — Clear Windows Temp
:: --------------------------------------------------
call :Log "Step 4 — Clearing Windows temp folder..."
echo Cleaning Windows temp...
del /f /s /q "C:\Windows\Temp\*" >nul 2>&1
for /d %%x in ("C:\Windows\Temp\*") do rd /s /q "%%x" >nul 2>&1
call :Log "Windows temp cleared."
echo [OK] Windows temp cleared.

:: --------------------------------------------------
:: Step 5 — Clear Prefetch (speeds up boot)
:: --------------------------------------------------
call :Log "Step 5 — Clearing prefetch cache..."
echo Clearing prefetch cache...
del /f /s /q "C:\Windows\Prefetch\*" >nul 2>&1
call :Log "Prefetch cache cleared."
echo [OK] Prefetch cache cleared.

:: --------------------------------------------------
:: Step 6 — Empty Recycle Bin
:: --------------------------------------------------
call :Log "Step 6 — Emptying Recycle Bin..."
echo Emptying Recycle Bin...
powershell.exe -NoProfile -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue" >nul 2>&1
call :Log "Recycle Bin emptied."
echo [OK] Recycle Bin emptied.

:: --------------------------------------------------
:: Step 7 — Clear Browser Caches
:: --------------------------------------------------
call :Log "Step 7 — Clearing browser caches..."
echo Clearing browser caches...

:: Chrome cache
if exist "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache" (
    del /f /s /q "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache\*" >nul 2>&1
    call :Log "Chrome cache cleared."
    echo [OK] Chrome cache cleared.
)

:: Edge cache
if exist "%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache" (
    del /f /s /q "%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache\*" >nul 2>&1
    call :Log "Edge cache cleared."
    echo [OK] Edge cache cleared.
)

:: Firefox cache
if exist "%APPDATA%\Mozilla\Firefox\Profiles" (
    for /d %%p in ("%APPDATA%\Mozilla\Firefox\Profiles\*") do (
        del /f /s /q "%%p\cache2\entries\*" >nul 2>&1
    )
    call :Log "Firefox cache cleared."
    echo [OK] Firefox cache cleared.
)

:: Internet Explorer / Legacy Edge
del /f /s /q "%LOCALAPPDATA%\Microsoft\Windows\INetCache\*" >nul 2>&1
call :Log "IE/Legacy cache cleared."

:: --------------------------------------------------
:: Step 8 — Stop Windows Update Services
:: --------------------------------------------------
call :Log "Step 8 — Stopping Windows Update services..."
echo Stopping Windows Update services...
net stop wuauserv >nul 2>&1
net stop bits >nul 2>&1
net stop dosvc >nul 2>&1
net stop cryptsvc >nul 2>&1
call :Log "Windows Update services stopped."
echo [OK] Update services stopped.

:: --------------------------------------------------
:: Step 9 — Clear Windows Update Cache
:: --------------------------------------------------
call :Log "Step 9 — Clearing Windows Update cache..."
echo Clearing Windows Update cache...
rd /s /q "C:\Windows\SoftwareDistribution\Download" >nul 2>&1
md "C:\Windows\SoftwareDistribution\Download" >nul 2>&1
rd /s /q "C:\Windows\SoftwareDistribution\DataStore" >nul 2>&1
md "C:\Windows\SoftwareDistribution\DataStore" >nul 2>&1
call :Log "Windows Update cache cleared."
echo [OK] Windows Update cache cleared.

:: --------------------------------------------------
:: Step 10 — Restart Update Services
:: --------------------------------------------------
call :Log "Step 10 — Restarting Windows Update services..."
echo Restarting update services...
net start cryptsvc >nul 2>&1
net start bits >nul 2>&1
net start wuauserv >nul 2>&1
net start dosvc >nul 2>&1
call :Log "Windows Update services restarted."
echo [OK] Update services restarted.

:: --------------------------------------------------
:: Step 11 — Flush DNS Cache
:: --------------------------------------------------
call :Log "Step 11 — Flushing DNS cache..."
echo Flushing DNS cache...
ipconfig /flushdns >nul 2>&1
call :Log "DNS cache flushed."
echo [OK] DNS cache flushed.

:: --------------------------------------------------
:: Step 12 — Reset Winsock and TCP/IP
:: --------------------------------------------------
call :Log "Step 12 — Resetting Winsock and TCP/IP..."
echo Resetting network stack...
netsh winsock reset >nul 2>&1
netsh int ip reset >nul 2>&1
netsh int ipv4 reset >nul 2>&1
netsh int ipv6 reset >nul 2>&1
call :Log "Network stack reset complete."
echo [OK] Network stack reset.

:: --------------------------------------------------
:: Step 13 — Clear Windows Font Cache
:: --------------------------------------------------
call :Log "Step 13 — Clearing font cache..."
echo Clearing font cache...
net stop "Windows Font Cache Service" >nul 2>&1
del /f /q "C:\Windows\ServiceProfiles\LocalService\AppData\Local\FontCache*" >nul 2>&1
net start "Windows Font Cache Service" >nul 2>&1
call :Log "Font cache cleared."
echo [OK] Font cache cleared.

:: --------------------------------------------------
:: Step 14 — Clear Windows Search Index
:: --------------------------------------------------
call :Log "Step 14 — Rebuilding Windows Search Index..."
echo Rebuilding search index...
net stop "Windows Search" >nul 2>&1
del /f /q "C:\ProgramData\Microsoft\Search\Data\Applications\Windows\Windows.edb" >nul 2>&1
net start "Windows Search" >nul 2>&1
call :Log "Windows Search index rebuild triggered."
echo [OK] Search index rebuild triggered.

:: --------------------------------------------------
:: Step 15 — Clear Thumbnail Cache
:: --------------------------------------------------
call :Log "Step 15 — Clearing thumbnail cache..."
echo Clearing thumbnail cache...
del /f /s /q "%LOCALAPPDATA%\Microsoft\Windows\Explorer\thumbcache_*.db" >nul 2>&1
call :Log "Thumbnail cache cleared."
echo [OK] Thumbnail cache cleared.

:: --------------------------------------------------
:: Step 16 — DISM Health Check and Repair
:: --------------------------------------------------
call :Log "Step 16 — Running DISM health check..."
echo Running DISM ScanHealth (this may take 5-10 minutes)...
DISM /Online /Cleanup-Image /ScanHealth >> "%LOGFILE%" 2>&1
if %errorlevel% neq 0 (
    call :Log "WARNING: DISM ScanHealth found issues. Running RestoreHealth..."
    echo [INFO] Issues found — running DISM RestoreHealth...
    DISM /Online /Cleanup-Image /RestoreHealth >> "%LOGFILE%" 2>&1
    call :Log "DISM RestoreHealth complete."
    echo [OK] DISM RestoreHealth complete.
) else (
    call :Log "DISM ScanHealth — no issues found."
    echo [OK] DISM ScanHealth — no issues found.
)

:: --------------------------------------------------
:: Step 17 — System File Checker
:: --------------------------------------------------
call :Log "Step 17 — Running System File Checker..."
echo Running SFC scan (this may take 5-10 minutes)...
sfc /scannow >> "%LOGFILE%" 2>&1
call :Log "SFC scan complete."
echo [OK] SFC scan complete.

:: --------------------------------------------------
:: Step 18 — Component Store Cleanup
:: --------------------------------------------------
call :Log "Step 18 — Cleaning WinSxS component store..."
echo Cleaning component store...
DISM /Online /Cleanup-Image /StartComponentCleanup >> "%LOGFILE%" 2>&1
call :Log "Component store cleanup complete."
echo [OK] WinSxS cleanup complete.

:: --------------------------------------------------
:: Step 19 — Disk Cleanup via CleanMgr
:: --------------------------------------------------
call :Log "Step 19 — Running automated disk cleanup..."
echo Running disk cleanup...
cleanmgr /sagerun:1 >nul 2>&1
if %errorlevel% neq 0 (
    cleanmgr /verylowdisk >nul 2>&1
)
call :Log "Disk cleanup complete."
echo [OK] Disk cleanup complete.

:: --------------------------------------------------
:: Step 20 — Optimize Drives (Defrag SSD/HDD)
:: --------------------------------------------------
call :Log "Step 20 — Optimizing C: drive..."
echo Optimizing C: drive...
defrag C: /U /V >> "%LOGFILE%" 2>&1
call :Log "Drive optimization complete."
echo [OK] Drive optimization complete.

:: --------------------------------------------------
:: Step 21 — Clear Event Logs
:: --------------------------------------------------
call :Log "Step 21 — Clearing Windows Event Logs..."
echo Clearing event logs...
for /F "tokens=*" %%G in ('wevtutil el') do (
    wevtutil cl "%%G" >nul 2>&1
)
call :Log "Event logs cleared."
echo [OK] Event logs cleared.

:: --------------------------------------------------
:: Step 22 — Record Disk Space After
:: --------------------------------------------------
call :Log "Step 22 — Recording disk space after cleanup..."
for /f "tokens=3" %%a in ('dir C:\ ^| find "bytes free"') do set FREEDSPACE_AFTER=%%a
call :Log "Disk free after: %FREEDSPACE_AFTER% bytes"

:: --------------------------------------------------
:: Step 23 — Generate Summary Report
:: --------------------------------------------------
call :Log "================================================="
call :Log "CLEANUP SUMMARY"
call :Log "Completed: %date% %time%"
call :Log "Machine  : %COMPUTERNAME%"
call :Log "Errors   : %ERRORCOUNT%"
call :Log "Disk before: %FREEDSPACE_BEFORE% bytes free"
call :Log "Disk after : %FREEDSPACE_AFTER% bytes free"
call :Log "Log saved to: %LOGFILE%"
call :Log "================================================="

echo.
echo =====================================================
echo  CLEANUP COMPLETED SUCCESSFULLY
echo =====================================================
echo  Machine  : %COMPUTERNAME%
echo  Errors   : %ERRORCOUNT%
echo  Log file : %LOGFILE%
echo =====================================================
echo.
echo  Recommended: Restart your computer to apply all changes.
echo.
pause
exit /b 0

:: --------------------------------------------------
:: Subroutine — Log with timestamp
:: --------------------------------------------------
:Log
echo [%time%] %~1 >> "%LOGFILE%"
exit /b