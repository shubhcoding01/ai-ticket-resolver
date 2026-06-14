# param(
#     [string]$MachineName,
#     [string]$Action = "repair",
#     [string]$TicketId,
#     [string]$RequesterEmail
# )

# Write-Host "===== OS REPAIR / DISK CLEANUP SCRIPT ====="
# Write-Host "Machine   : $MachineName"
# Write-Host "Action    : $Action"
# Write-Host "Ticket ID : $TicketId"

# try {
#     $ScriptBlock = {
#         Write-Host "Running System File Checker (sfc /scannow)..."
#         sfc /scannow

#         Write-Host "Running DISM health restore..."
#         DISM /Online /Cleanup-Image /RestoreHealth

#         Write-Host "Cleaning temp files..."
#         Remove-Item -Path "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
#         Remove-Item -Path "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue

#         $Drive = Get-PSDrive C
#         $FreeGB = [math]::Round($Drive.Free / 1GB, 2)
#         Write-Host "Free disk space on C: $FreeGB GB"

#         Write-Host "OS repair and cleanup complete."
#     }

#     Invoke-Command -ComputerName $MachineName `
#                    -ScriptBlock $ScriptBlock `
#                    -ErrorAction Stop

#     exit 0

# } catch {
#     Write-Host "ERROR: Failed on $MachineName — $_"
#     exit 1
# }


<#
.SYNOPSIS
    Remote disk cleanup and OS repair for ICICI Bank IT
.DESCRIPTION
    Clears temp files, runs SFC and DISM, clears update cache,
    removes old log files, and frees disk space on a remote machine.
.PARAMETER MachineName
    Target machine name
.PARAMETER TicketId
    Freshdesk ticket ID
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$MachineName,

    [string]$TicketId       = "0",
    [string]$RequesterEmail = "",
    [int]$MinFreeGB         = 5
)

$ErrorActionPreference = "Continue"

$LogDir  = "$PSScriptRoot\logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$LogFile = "$LogDir\disk_cleanup_${TicketId}_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Entry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$Level] $Message"
    Add-Content -Path $LogFile -Value $Entry
    Write-Output $Entry
}

Write-Log "=== Disk Cleanup Script Started ==="
Write-Log "Ticket     : $TicketId"
Write-Log "Machine    : $MachineName"
Write-Log "Min Free GB: $MinFreeGB"

$Ping = Test-Connection -ComputerName $MachineName -Count 2 -Quiet -ErrorAction SilentlyContinue
if (-not $Ping) {
    Write-Log "Machine $MachineName is not reachable." "ERROR"
    Write-Output "FAILED: Machine $MachineName is offline."
    exit 1
}

$RemoteScript = {
    param($MinFreeGB)
    $results = @()

    # Check disk space before
    $Drive   = Get-PSDrive -Name C -ErrorAction SilentlyContinue
    $FreeBefore = [math]::Round($Drive.Free / 1GB, 2)
    $results += "Disk free before cleanup: $FreeBefore GB"

    # Clear user temp
    Remove-Item -Path "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
    $results += "User temp files cleared."

    # Clear Windows temp
    Remove-Item -Path "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
    $results += "Windows temp files cleared."

    # Clear Windows Update cache
    Stop-Service -Name wuauserv -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "C:\Windows\SoftwareDistribution\Download\*" -Recurse -Force -ErrorAction SilentlyContinue
    Start-Service -Name wuauserv -ErrorAction SilentlyContinue
    $results += "Windows Update download cache cleared."

    # Clear prefetch
    Remove-Item -Path "C:\Windows\Prefetch\*" -Force -ErrorAction SilentlyContinue
    $results += "Prefetch cache cleared."

    # Clear browser caches
    Remove-Item -Path "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache\*" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache\*" -Recurse -Force -ErrorAction SilentlyContinue
    $results += "Browser caches cleared."

    # Clear old log files over 30 days
    $LogPaths = @(
        "C:\Windows\Logs",
        "C:\Windows\System32\winevt\Logs",
        "$env:LOCALAPPDATA\Temp"
    )
    foreach ($LogPath in $LogPaths) {
        Get-ChildItem -Path $LogPath -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) -and -not $_.PSIsContainer } |
        Remove-Item -Force -ErrorAction SilentlyContinue
    }
    $results += "Old log files (30+ days) removed."

    # Empty Recycle Bin
    Clear-RecycleBin -Force -ErrorAction SilentlyContinue
    $results += "Recycle Bin emptied."

    # Run SFC
    $SFCResult = sfc /scannow 2>&1
    $results += "SFC scan completed."

    # Run DISM
    $DISMResult = DISM /Online /Cleanup-Image /RestoreHealth 2>&1
    $results += "DISM RestoreHealth completed."

    # Check disk space after
    $DriveAfter = Get-PSDrive -Name C -ErrorAction SilentlyContinue
    $FreeAfter  = [math]::Round($DriveAfter.Free / 1GB, 2)
    $Freed      = [math]::Round($FreeAfter - $FreeBefore, 2)
    $results += "Disk free after cleanup: $FreeAfter GB"
    $results += "Total space freed: $Freed GB"

    if ($FreeAfter -lt $MinFreeGB) {
        $results += "WARNING: Disk still below $MinFreeGB GB free. Manual intervention may be needed."
    }

    return $results
}

try {
    $Output = Invoke-Command -ComputerName $MachineName `
                             -ScriptBlock $RemoteScript `
                             -ArgumentList $MinFreeGB `
                             -ErrorAction Stop

    foreach ($line in $Output) { Write-Log $line }

    Write-Output "SUCCESS: Disk cleanup and SFC/DISM repair complete on $MachineName."
    exit 0

} catch {
    Write-Log "Remote execution failed: $_" "ERROR"
    Write-Output "FAILED: Disk cleanup failed on $MachineName — $_"
    exit 1
}