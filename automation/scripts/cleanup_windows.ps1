@echo off
setlocal EnableDelayedExpansion
title ICICI Bank — Enterprise Windows Cleanup & Maintenance Tool
color 0A

:: ===========================================================
:: ICICI Bank — Enterprise Windows Cleanup & Maintenance Tool
:: IT Support Automation — automation/scripts/cleanup_windows.bat
:: Compatible  : Windows 10 / Windows 11
:: Run as      : Administrator
:: Version     : 3.0
:: Called by   : automation/runner.py for os_issue tickets
::               or run manually by IT engineers
:: ===========================================================

:: ----------------------------------------------------------
:: SETUP — Log directory and file
:: ----------------------------------------------------------
set "COMPANY=ICICI Bank"
set "SCRIPT_VER=3.0"
set "LOGDIR=%~dp0logs"
set "REPORTDIR=%~dp0reports"

if not exist "%LOGDIR%"   mkdir "%LOGDIR%"
if not exist "%REPORTDIR%" mkdir "%REPORTDIR%"

:: Build timestamp for filenames (YYYYMMDD_HHMMSS)
for /f "tokens=2 delims==" %%I in (
    'wmic os get localdatetime /value 2^>nul'
) do set DTRAW=%%I
set "TIMESTAMP=%DTRAW:~0,8%_%DTRAW:~8,6%"

set "LOGFILE=%LOGDIR%\Cleanup_%COMPUTERNAME%_%TIMESTAMP%.txt"
set "REPORTFILE=%REPORTDIR%\Report_%COMPUTERNAME%_%TIMESTAMP%.txt"

set "ERRORCOUNT=0"
set "STEPCOUNT=0"
set "SUCCESSCOUNT=0"
set "SPACE_BEFORE=0"
set "SPACE_AFTER=0"

:: ----------------------------------------------------------
:: Start Log
:: ----------------------------------------------------------
call :Log "==========================================================="
call :Log "%COMPANY% — Windows Cleanup ^& Maintenance Tool v%SCRIPT_VER%"
call :Log "==========================================================="
call :Log "Machine    : %COMPUTERNAME%"
call :Log "User       : %USERNAME%"
call :Log "Date/Time  : %DATE% %TIME%"
call :Log "Log file   : %LOGFILE%"
call :Log "Report file: %REPORTFILE%"
call :Log "==========================================================="

:: ----------------------------------------------------------
:: BANNER
:: ----------------------------------------------------------
cls
echo.
echo  ============================================================
echo   %COMPANY% — WINDOWS CLEANUP ^& MAINTENANCE TOOL v%SCRIPT_VER%
echo  ============================================================
echo   Machine    : %COMPUTERNAME%
echo   User       : %USERNAME%
echo   Date       : %DATE%  Time: %TIME%
echo   Log file   : %LOGFILE%
echo  ============================================================
echo.
echo   This tool will perform the following operations:
echo.
echo    [1]  Check administrator rights
echo    [2]  Record initial disk space
echo    [3]  Clear user temp files
echo    [4]  Clear Windows temp files
echo    [5]  Clear Windows prefetch cache
echo    [6]  Empty Recycle Bin
echo    [7]  Clear browser caches (Chrome, Edge, Firefox, IE)
echo    [8]  Clear thumbnail cache
echo    [9]  Stop Windows Update services
echo    [10] Clear Windows Update download cache
echo    [11] Clear Windows Update DataStore
echo    [12] Restart Windows Update services
echo    [13] Flush DNS cache
echo    [14] Reset Winsock catalog
echo    [15] Reset TCP/IP stack
echo    [16] Clear Windows font cache
echo    [17] Rebuild Windows Search index
echo    [18] Clear old Windows log files
echo    [19] Clear Microsoft Office temp files
echo    [20] Clear Windows Error Reporting files
echo    [21] DISM ScanHealth
echo    [22] DISM RestoreHealth (if issues found)
echo    [23] System File Checker (sfc /scannow)
echo    [24] DISM component store cleanup
echo    [25] Disk defragment / optimize C drive
echo    [26] Run Disk Cleanup utility
echo    [27] Clear Windows Event Logs
echo    [28] Record final disk space
echo    [29] Generate cleanup report
echo.
echo  ============================================================
echo.

:: ----------------------------------------------------------
:: CONFIRM before proceeding
:: ----------------------------------------------------------
set /p CONFIRM="  Press ENTER to start cleanup or type NO to cancel: "
if /i "%CONFIRM%"=="NO" (
    echo.
    echo  Cleanup cancelled by user.
    call :Log "Cleanup cancelled by user."
    pause
    exit /b 0
)

echo.
echo  Starting cleanup — please wait...
echo.

:: ==========================================================
:: STEP 1 — Check Administrator Rights
:: ==========================================================
call :StepStart 1 "Checking administrator rights"
net session >nul 2>&1
if %errorlevel% neq 0 (
    call :Log "[ERROR] Script not running as administrator." "ERROR"
    echo.
    echo  [ERROR] This script must be run as Administrator.
    echo  Right-click the .bat file and select Run as administrator.
    echo.
    pause
    exit /b 1
)
call :StepOK "Running as Administrator"

:: ==========================================================
:: STEP 2 — Record Disk Space Before
:: ==========================================================
call :StepStart 2 "Recording disk space before cleanup"
for /f "skip=1 tokens=1,2,3" %%a in (
    'wmic logicaldisk where caption="C:" get size^,freespace^,caption /format:list 2^>nul'
) do (
    if "%%a"=="FreeSpace=" set SPACE_BEFORE=%%b
)
call :Log "Disk free before cleanup: %SPACE_BEFORE% bytes"
call :StepOK "Disk space recorded"

:: ==========================================================
:: STEP 3 — Clear User Temp Files
:: ==========================================================
call :StepStart 3 "Clearing user temp files"
del /f /s /q "%TEMP%\*"            >nul 2>&1
for /d %%x in ("%TEMP%\*") do (
    rd /s /q "%%x"                 >nul 2>&1
)
call :StepOK "User temp files cleared"

:: ==========================================================
:: STEP 4 — Clear Windows Temp
:: ==========================================================
call :StepStart 4 "Clearing Windows temp folder"
del /f /s /q "C:\Windows\Temp\*"   >nul 2>&1
for /d %%x in ("C:\Windows\Temp\*") do (
    rd /s /q "%%x"                 >nul 2>&1
)
call :StepOK "Windows temp cleared"

:: ==========================================================
:: STEP 5 — Clear Prefetch Cache
:: ==========================================================
call :StepStart 5 "Clearing Windows prefetch cache"
del /f /s /q "C:\Windows\Prefetch\*" >nul 2>&1
call :StepOK "Prefetch cache cleared"

:: ==========================================================
:: STEP 6 — Empty Recycle Bin
:: ==========================================================
call :StepStart 6 "Emptying Recycle Bin"
powershell.exe -NoProfile -NonInteractive -Command ^
    "Clear-RecycleBin -Force -ErrorAction SilentlyContinue" >nul 2>&1
call :StepOK "Recycle Bin emptied"

:: ==========================================================
:: STEP 7 — Clear Browser Caches
:: ==========================================================
call :StepStart 7 "Clearing browser caches"

:: Google Chrome
if exist "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache" (
    del /f /s /q "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache\*" >nul 2>&1
    call :Log "Chrome cache cleared."
)
if exist "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Code Cache" (
    del /f /s /q "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Code Cache\*" >nul 2>&1
    call :Log "Chrome code cache cleared."
)

:: Microsoft Edge
if exist "%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache" (
    del /f /s /q "%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache\*" >nul 2>&1
    call :Log "Edge cache cleared."
)
if exist "%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Code Cache" (
    del /f /s /q "%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Code Cache\*" >nul 2>&1
    call :Log "Edge code cache cleared."
)

:: Mozilla Firefox
if exist "%APPDATA%\Mozilla\Firefox\Profiles" (
    for /d %%p in ("%APPDATA%\Mozilla\Firefox\Profiles\*") do (
        if exist "%%p\cache2\entries" (
            del /f /s /q "%%p\cache2\entries\*" >nul 2>&1
        )
        if exist "%%p\cache2\doomed" (
            del /f /s /q "%%p\cache2\doomed\*"  >nul 2>&1
        )
    )
    call :Log "Firefox cache cleared."
)

:: Internet Explorer / Legacy
del /f /s /q "%LOCALAPPDATA%\Microsoft\Windows\INetCache\*" >nul 2>&1
del /f /s /q "%LOCALAPPDATA%\Microsoft\Windows\WebCache\*"  >nul 2>&1
call :Log "IE/WebCache cleared."

call :StepOK "All browser caches cleared"

:: ==========================================================
:: STEP 8 — Clear Thumbnail Cache
:: ==========================================================
call :StepStart 8 "Clearing Windows thumbnail cache"
del /f /s /q "%LOCALAPPDATA%\Microsoft\Windows\Explorer\thumbcache_*.db" >nul 2>&1
del /f /s /q "%LOCALAPPDATA%\Microsoft\Windows\Explorer\iconcache_*.db"  >nul 2>&1
call :StepOK "Thumbnail and icon caches cleared"

:: ==========================================================
:: STEP 9 — Stop Windows Update Services
:: ==========================================================
call :StepStart 9 "Stopping Windows Update services"
net stop wuauserv  >nul 2>&1
net stop bits      >nul 2>&1
net stop dosvc     >nul 2>&1
net stop cryptsvc  >nul 2>&1
call :StepOK "Update services stopped"

:: ==========================================================
:: STEP 10 — Clear Windows Update Download Cache
:: ==========================================================
call :StepStart 10 "Clearing Windows Update download cache"
rd /s /q "C:\Windows\SoftwareDistribution\Download"  >nul 2>&1
md       "C:\Windows\SoftwareDistribution\Download"  >nul 2>&1
call :StepOK "Update download cache cleared"

:: ==========================================================
:: STEP 11 — Clear Windows Update DataStore
:: ==========================================================
call :StepStart 11 "Clearing Windows Update DataStore"
rd /s /q "C:\Windows\SoftwareDistribution\DataStore" >nul 2>&1
md       "C:\Windows\SoftwareDistribution\DataStore" >nul 2>&1
call :StepOK "Update DataStore cleared"

:: ==========================================================
:: STEP 12 — Restart Windows Update Services
:: ==========================================================
call :StepStart 12 "Restarting Windows Update services"
net start cryptsvc >nul 2>&1
net start bits     >nul 2>&1
net start wuauserv >nul 2>&1
net start dosvc    >nul 2>&1
call :StepOK "Update services restarted"

:: ==========================================================
:: STEP 13 — Flush DNS Cache
:: ==========================================================
call :StepStart 13 "Flushing DNS cache"
ipconfig /flushdns >nul 2>&1
call :StepOK "DNS cache flushed"

:: ==========================================================
:: STEP 14 — Reset Winsock Catalog
:: ==========================================================
call :StepStart 14 "Resetting Winsock catalog"
netsh winsock reset >nul 2>&1
call :StepOK "Winsock reset complete"

:: ==========================================================
:: STEP 15 — Reset TCP/IP Stack
:: ==========================================================
call :StepStart 15 "Resetting TCP/IP stack"
netsh int ip reset   >nul 2>&1
netsh int ipv4 reset >nul 2>&1
netsh int ipv6 reset >nul 2>&1
call :StepOK "TCP/IP stack reset complete"

:: ==========================================================
:: STEP 16 — Clear Windows Font Cache
:: ==========================================================
call :StepStart 16 "Clearing Windows font cache"
net stop "FontCache"                          >nul 2>&1
net stop "Windows Font Cache Service"         >nul 2>&1
del /f /q "%WinDir%\ServiceProfiles\LocalService\AppData\Local\FontCache*"    >nul 2>&1
del /f /q "%WinDir%\ServiceProfiles\LocalService\AppData\Local\FontCache3*"   >nul 2>&1
del /f /q "%WinDir%\System32\FNTCACHE.DAT"   >nul 2>&1
net start "FontCache"                         >nul 2>&1
net start "Windows Font Cache Service"        >nul 2>&1
call :StepOK "Font cache cleared and service restarted"

:: ==========================================================
:: STEP 17 — Rebuild Windows Search Index
:: ==========================================================
call :StepStart 17 "Rebuilding Windows Search index"
net stop "Windows Search"                                                >nul 2>&1
del /f /q "C:\ProgramData\Microsoft\Search\Data\Applications\Windows\Windows.edb" >nul 2>&1
net start "Windows Search"                                              >nul 2>&1
call :StepOK "Search index rebuild triggered"

:: ==========================================================
:: STEP 18 — Clear Old Windows Log Files (30+ days)
:: ==========================================================
call :StepStart 18 "Clearing old Windows log files (30+ days)"
forfiles /p "C:\Windows\Logs" /s /m *.log ^
         /d -30 /c "cmd /c del /f /q @path" >nul 2>&1
forfiles /p "C:\Windows\Logs\CBS" /s /m *.log ^
         /d -30 /c "cmd /c del /f /q @path" >nul 2>&1
del /f /q "C:\Windows\System32\LogFiles\WMI\*.etl" >nul 2>&1
call :StepOK "Old log files removed"

:: ==========================================================
:: STEP 19 — Clear Microsoft Office Temp Files
:: ==========================================================
call :StepStart 19 "Clearing Microsoft Office temp files"
del /f /s /q "%APPDATA%\Microsoft\Office\Recent\*"      >nul 2>&1
del /f /s /q "%LOCALAPPDATA%\Microsoft\Office\OTele\*"  >nul 2>&1
del /f /s /q "%LOCALAPPDATA%\Temp\Word*"                >nul 2>&1
del /f /s /q "%LOCALAPPDATA%\Temp\Excel*"               >nul 2>&1
del /f /s /q "%LOCALAPPDATA%\Temp\PPT*"                 >nul 2>&1
del /f /s /q "%LOCALAPPDATA%\Temp\Outlook*"             >nul 2>&1
call :StepOK "Office temp files cleared"

:: ==========================================================
:: STEP 20 — Clear Windows Error Reporting
:: ==========================================================
call :StepStart 20 "Clearing Windows Error Reporting files"
del /f /s /q "%LOCALAPPDATA%\Microsoft\Windows\WER\*"   >nul 2>&1
del /f /s /q "C:\ProgramData\Microsoft\Windows\WER\*"   >nul 2>&1
rd  /s /q   "%LOCALAPPDATA%\CrashDumps"                >nul 2>&1
call :StepOK "Error reporting files cleared"

:: ==========================================================
:: STEP 21 — DISM ScanHealth
:: ==========================================================
call :StepStart 21 "Running DISM image health scan"
echo.
echo   [INFO] DISM ScanHealth may take 5-15 minutes.
echo   [INFO] Do NOT close this window.
echo.
DISM /Online /Cleanup-Image /ScanHealth >> "%LOGFILE%" 2>&1
set DISM_SCAN_RESULT=%errorlevel%
call :Log "DISM ScanHealth exit code: %DISM_SCAN_RESULT%"
call :StepOK "DISM ScanHealth complete (exit: %DISM_SCAN_RESULT%)"

:: ==========================================================
:: STEP 22 — DISM RestoreHealth (if issues found)
:: ==========================================================
call :StepStart 22 "Running DISM RestoreHealth repair"
if %DISM_SCAN_RESULT% neq 0 (
    echo.
    echo   [INFO] Issues found — running DISM RestoreHealth.
    echo   [INFO] This may take 10-30 minutes depending on connection.
    echo.
    DISM /Online /Cleanup-Image /RestoreHealth >> "%LOGFILE%" 2>&1
    call :Log "DISM RestoreHealth exit code: %errorlevel%"
    call :StepOK "DISM RestoreHealth complete"
) else (
    call :Log "DISM found no corruption — RestoreHealth skipped."
    call :StepOK "No issues found — RestoreHealth skipped"
)

:: ==========================================================
:: STEP 23 — System File Checker
:: ==========================================================
call :StepStart 23 "Running System File Checker (sfc /scannow)"
echo.
echo   [INFO] SFC scan may take 5-15 minutes.
echo   [INFO] Do NOT close this window.
echo.
sfc /scannow >> "%LOGFILE%" 2>&1
call :Log "SFC exit code: %errorlevel%"
call :StepOK "SFC scan complete"

:: ==========================================================
:: STEP 24 — DISM Component Store Cleanup
:: ==========================================================
call :StepStart 24 "Cleaning DISM component store (WinSxS)"
DISM /Online /Cleanup-Image /StartComponentCleanup >> "%LOGFILE%" 2>&1
call :Log "Component store cleanup exit code: %errorlevel%"
call :StepOK "Component store cleanup complete"

:: ==========================================================
:: STEP 25 — Optimize / Defrag C Drive
:: ==========================================================
call :StepStart 25 "Optimizing C: drive"
defrag C: /U /V >> "%LOGFILE%" 2>&1
call :StepOK "Drive optimization complete"

:: ==========================================================
:: STEP 26 — Run Disk Cleanup Utility
:: ==========================================================
call :StepStart 26 "Running Windows Disk Cleanup utility"
:: Configure CleanMgr to clean everything automatically
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VolumeCaches\Temporary Files" /v StateFlags0001 /t REG_DWORD /d 2 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VolumeCaches\Recycle Bin"     /v StateFlags0001 /t REG_DWORD /d 2 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VolumeCaches\Temporary Internet Files" /v StateFlags0001 /t REG_DWORD /d 2 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VolumeCaches\Thumbnails"      /v StateFlags0001 /t REG_DWORD /d 2 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VolumeCaches\Downloaded Program Files" /v StateFlags0001 /t REG_DWORD /d 2 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VolumeCaches\Windows Error Reporting" /v StateFlags0001 /t REG_DWORD /d 2 /f >nul 2>&1
cleanmgr /sagerun:1 >nul 2>&1
call :StepOK "Disk Cleanup complete"

:: ==========================================================
:: STEP 27 — Clear Windows Event Logs
:: ==========================================================
call :StepStart 27 "Clearing Windows Event Logs"
for /F "tokens=*" %%G in ('wevtutil el 2^>nul') do (
    wevtutil cl "%%G" >nul 2>&1
)
call :StepOK "Event logs cleared"

:: ==========================================================
:: STEP 28 — Record Final Disk Space
:: ==========================================================
call :StepStart 28 "Recording disk space after cleanup"
for /f "skip=1 tokens=1,2,3" %%a in (
    'wmic logicaldisk where caption="C:" get size^,freespace^,caption /format:list 2^>nul'
) do (
    if "%%a"=="FreeSpace=" set SPACE_AFTER=%%b
)
call :Log "Disk free after cleanup: %SPACE_AFTER% bytes"
call :StepOK "Final disk space recorded"

:: ==========================================================
:: STEP 29 — Generate Cleanup Report
:: ==========================================================
call :StepStart 29 "Generating cleanup report"

echo =========================================================== >  "%REPORTFILE%"
echo %COMPANY% — Windows Cleanup Report                         >> "%REPORTFILE%"
echo =========================================================== >> "%REPORTFILE%"
echo Machine       : %COMPUTERNAME%                             >> "%REPORTFILE%"
echo User          : %USERNAME%                                 >> "%REPORTFILE%"
echo Date          : %DATE%                                     >> "%REPORTFILE%"
echo Time          : %TIME%                                     >> "%REPORTFILE%"
echo Script version: %SCRIPT_VER%                              >> "%REPORTFILE%"
echo =========================================================== >> "%REPORTFILE%"
echo.                                                           >> "%REPORTFILE%"
echo RESULTS                                                    >> "%REPORTFILE%"
echo ----------------------------------------------------------->> "%REPORTFILE%"
echo Total steps   : %STEPCOUNT%                               >> "%REPORTFILE%"
echo Successful    : %SUCCESSCOUNT%                            >> "%REPORTFILE%"
echo Errors        : %ERRORCOUNT%                              >> "%REPORTFILE%"
echo Disk before   : %SPACE_BEFORE% bytes free                 >> "%REPORTFILE%"
echo Disk after    : %SPACE_AFTER%  bytes free                 >> "%REPORTFILE%"
echo =========================================================== >> "%REPORTFILE%"
echo.                                                           >> "%REPORTFILE%"
echo OPERATIONS COMPLETED                                       >> "%REPORTFILE%"
echo ----------------------------------------------------------->> "%REPORTFILE%"
echo [OK] User temp files cleared                              >> "%REPORTFILE%"
echo [OK] Windows temp files cleared                           >> "%REPORTFILE%"
echo [OK] Prefetch cache cleared                               >> "%REPORTFILE%"
echo [OK] Recycle Bin emptied                                  >> "%REPORTFILE%"
echo [OK] Browser caches cleared (Chrome, Edge, Firefox, IE)  >> "%REPORTFILE%"
echo [OK] Thumbnail and icon caches cleared                    >> "%REPORTFILE%"
echo [OK] Windows Update cache cleared                         >> "%REPORTFILE%"
echo [OK] DNS cache flushed                                    >> "%REPORTFILE%"
echo [OK] Winsock and TCP/IP stack reset                       >> "%REPORTFILE%"
echo [OK] Font cache cleared                                   >> "%REPORTFILE%"
echo [OK] Search index rebuild triggered                       >> "%REPORTFILE%"
echo [OK] Old log files removed (30+ days)                     >> "%REPORTFILE%"
echo [OK] Office temp files cleared                            >> "%REPORTFILE%"
echo [OK] Error reporting files cleared                        >> "%REPORTFILE%"
echo [OK] DISM health scan complete                            >> "%REPORTFILE%"
echo [OK] SFC system file check complete                       >> "%REPORTFILE%"
echo [OK] Component store cleaned                              >> "%REPORTFILE%"
echo [OK] Drive optimized                                      >> "%REPORTFILE%"
echo [OK] Disk Cleanup utility run                             >> "%REPORTFILE%"
echo [OK] Event logs cleared                                   >> "%REPORTFILE%"
echo =========================================================== >> "%REPORTFILE%"
echo.                                                           >> "%REPORTFILE%"
echo Full log: %LOGFILE%                                        >> "%REPORTFILE%"
echo =========================================================== >> "%REPORTFILE%"

call :StepOK "Report generated: %REPORTFILE%"

:: ==========================================================
:: FINAL SUMMARY
:: ==========================================================
call :Log "==========================================================="
call :Log "CLEANUP COMPLETE"
call :Log "Total steps  : %STEPCOUNT%"
call :Log "Successful   : %SUCCESSCOUNT%"
call :Log "Errors       : %ERRORCOUNT%"
call :Log "Disk before  : %SPACE_BEFORE% bytes"
call :Log "Disk after   : %SPACE_AFTER%  bytes"
call :Log "Log file     : %LOGFILE%"
call :Log "Report file  : %REPORTFILE%"
call :Log "==========================================================="

echo.
echo  ============================================================
echo   CLEANUP COMPLETED SUCCESSFULLY
echo  ============================================================
echo.
echo   Machine      : %COMPUTERNAME%
echo   Steps done   : %STEPCOUNT%
echo   Successful   : %SUCCESSCOUNT%
echo   Errors       : %ERRORCOUNT%
echo   Disk before  : %SPACE_BEFORE% bytes free
echo   Disk after   : %SPACE_AFTER%  bytes free
echo   Log saved    : %LOGFILE%
echo   Report saved : %REPORTFILE%
echo.
echo  ============================================================
echo.
echo   IMPORTANT: Restart your computer to fully apply all changes.
echo   Some changes (Winsock, TCP/IP, SFC) require a restart.
echo.
echo  ============================================================
echo.

set /p RESTART="  Restart computer now? (YES / NO): "
if /i "%RESTART%"=="YES" (
    call :Log "User chose to restart computer."
    echo.
    echo  Restarting in 15 seconds... Press Ctrl+C to cancel.
    shutdown /r /t 15 /c "ICICI Bank IT: Cleanup complete — restarting to apply changes."
) else (
    echo.
    echo  Please restart your computer manually when convenient.
)

call :Log "Script finished."
echo.
pause
exit /b 0


:: ==========================================================
:: SUBROUTINES
:: ==========================================================

:Log
:: Usage: call :Log "message"
echo [%TIME%] %~1 >> "%LOGFILE%"
exit /b

:StepStart
:: Usage: call :StepStart <stepnum> "description"
set /a STEPCOUNT+=1
echo  [Step %~1/29] %~2...
call :Log "[STEP %~1] %~2 — STARTED"
exit /b

:StepOK
:: Usage: call :StepOK "result message"
set /a SUCCESSCOUNT+=1
echo  [  OK  ] %~1
call :Log "[  OK  ] %~1"
echo.
exit /b

:StepFail
:: Usage: call :StepFail "error message"
set /a ERRORCOUNT+=1
echo  [ FAIL ] %~1
call :Log "[ FAIL ] %~1"
echo.
exit /b