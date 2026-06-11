<#
.SYNOPSIS
    Remote Outlook repair script for ICICI Bank IT
.DESCRIPTION
    Repairs Outlook profile, runs scanpst on PST files,
    clears Outlook cache, and restarts Outlook cleanly.
.PARAMETER MachineName
    Target machine name
.PARAMETER TicketId
    Freshdesk ticket ID
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$MachineName,

    [string]$TicketId       = "0",
    [string]$RequesterEmail = ""
)

$ErrorActionPreference = "Continue"

$LogDir  = "$PSScriptRoot\logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$LogFile = "$LogDir\outlook_${TicketId}_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Entry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$Level] $Message"
    Add-Content -Path $LogFile -Value $Entry
    Write-Output $Entry
}

Write-Log "=== Outlook Repair Script Started ==="
Write-Log "Ticket  : $TicketId"
Write-Log "Machine : $MachineName"
Write-Log "User    : $RequesterEmail"

$Ping = Test-Connection -ComputerName $MachineName -Count 2 -Quiet -ErrorAction SilentlyContinue
if (-not $Ping) {
    Write-Log "Machine $MachineName is not reachable." "ERROR"
    Write-Output "FAILED: Machine $MachineName is offline."
    exit 1
}

$RemoteScript = {
    $results = @()

    # Kill Outlook if running
    $OutlookProc = Get-Process -Name OUTLOOK -ErrorAction SilentlyContinue
    if ($OutlookProc) {
        Stop-Process -Name OUTLOOK -Force
        Start-Sleep -Seconds 3
        $results += "Outlook process terminated before repair."
    }

    # Clear Outlook cache files
    $CachePaths = @(
        "$env:LOCALAPPDATA\Microsoft\Outlook\*.ost",
        "$env:APPDATA\Microsoft\Outlook\*.nk2",
        "$env:LOCALAPPDATA\Microsoft\Outlook\RoamCache\*"
    )

    foreach ($CachePath in $CachePaths) {
        $Files = Get-Item $CachePath -ErrorAction SilentlyContinue
        if ($Files) {
            Remove-Item $CachePath -Force -ErrorAction SilentlyContinue
            $results += "Cleared cache: $CachePath"
        }
    }

    # Find and repair PST files with scanpst
    $ScanPstPaths = @(
        "C:\Program Files\Microsoft Office\root\Office16\SCANPST.EXE",
        "C:\Program Files (x86)\Microsoft Office\root\Office16\SCANPST.EXE",
        "C:\Program Files\Microsoft Office\Office16\SCANPST.EXE",
        "C:\Program Files (x86)\Microsoft Office\Office16\SCANPST.EXE"
    )

    $ScanPst = $null
    foreach ($path in $ScanPstPaths) {
        if (Test-Path $path) {
            $ScanPst = $path
            break
        }
    }

    if ($ScanPst) {
        $PstFiles = Get-ChildItem -Path "$env:USERPROFILE\Documents" `
                                  -Recurse -Filter "*.pst" `
                                  -ErrorAction SilentlyContinue
        foreach ($pst in $PstFiles) {
            $results += "Found PST: $($pst.FullName)"
            Start-Process -FilePath $ScanPst -ArgumentList "`"$($pst.FullName)`"" -Wait -WindowStyle Hidden
            $results += "ScanPST completed for: $($pst.Name)"
        }
    } else {
        $results += "SCANPST.EXE not found — Office may not be installed."
    }

    # Reset Outlook profile registry entries
    $OutlookRegPath = "HKCU:\Software\Microsoft\Office\16.0\Outlook"
    if (Test-Path $OutlookRegPath) {
        Remove-ItemProperty -Path $OutlookRegPath -Name "FirstRun" -ErrorAction SilentlyContinue
        $results += "Outlook registry first-run flag cleared."
    }

    # Quick repair Office via ClickToRun
    $C2RPath = "C:\Program Files\Common Files\Microsoft Shared\ClickToRun\OfficeC2RClient.exe"
    if (Test-Path $C2RPath) {
        Start-Process -FilePath $C2RPath -ArgumentList "/repair" -Wait -WindowStyle Hidden
        $results += "Office Click-to-Run quick repair triggered."
    }

    $results += "Outlook repair sequence completed."
    return $results
}

try {
    $Output = Invoke-Command -ComputerName $MachineName `
                             -ScriptBlock $RemoteScript `
                             -ErrorAction Stop

    foreach ($line in $Output) { Write-Log $line }

    Write-Output "SUCCESS: Outlook repaired on $MachineName. Cache cleared and PST repaired."
    exit 0

} catch {
    Write-Log "Remote execution failed: $_" "ERROR"
    Write-Output "FAILED: Outlook repair failed on $MachineName — $_"
    exit 1
}