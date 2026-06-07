# param(
#     [string]$MachineName,
#     [string]$ScanType = "full",
#     [string]$TicketId,
#     [string]$RequesterEmail
# )

# Write-Host "===== ANTIVIRUS UPDATE SCRIPT ====="
# Write-Host "Machine   : $MachineName"
# Write-Host "Scan Type : $ScanType"
# Write-Host "Ticket ID : $TicketId"

# try {
#     $ScriptBlock = {
#         param($ScanType)

#         Write-Host "Updating Windows Defender definitions..."
#         Update-MpSignature -ErrorAction Stop
#         Write-Host "Definitions updated successfully."

#         if ($ScanType -eq "full") {
#             Write-Host "Starting full antivirus scan..."
#             Start-MpScan -ScanType FullScan -ErrorAction Stop
#         } else {
#             Write-Host "Starting quick antivirus scan..."
#             Start-MpScan -ScanType QuickScan -ErrorAction Stop
#         }

#         $Status = Get-MpComputerStatus
#         Write-Host "AV Status     : $($Status.AMRunningMode)"
#         Write-Host "Last Updated  : $($Status.AntivirusSignatureLastUpdated)"
#         Write-Host "Real-time     : $($Status.RealTimeProtectionEnabled)"
#     }

#     Invoke-Command -ComputerName $MachineName `
#                    -ScriptBlock $ScriptBlock `
#                    -ArgumentList $ScanType `
#                    -ErrorAction Stop

#     Write-Host "Antivirus update and scan complete on $MachineName."
#     exit 0

# } catch {
#     Write-Host "ERROR: Failed on $MachineName — $_"
#     exit 1
# }


<#
.SYNOPSIS
    Remote antivirus update and scan trigger for ICICI Bank IT
.DESCRIPTION
    Updates antivirus definitions and triggers a scan on a
    remote machine. Supports Windows Defender and Symantec.
.PARAMETER MachineName
    Target machine name
.PARAMETER TicketId
    Freshdesk ticket ID for logging
.PARAMETER ScanType
    Type of scan: quick or full (default: full)
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$MachineName,

    [string]$TicketId  = "0",
    [string]$ScanType  = "full",
    [string]$RequesterEmail = ""
)

$ErrorActionPreference = "Continue"

$LogDir  = "$PSScriptRoot\logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$LogFile = "$LogDir\antivirus_${TicketId}_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Entry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$Level] $Message"
    Add-Content -Path $LogFile -Value $Entry
    Write-Output $Entry
}

Write-Log "=== Antivirus Update Script Started ==="
Write-Log "Ticket   : $TicketId"
Write-Log "Machine  : $MachineName"
Write-Log "ScanType : $ScanType"

# ---- Verify Machine is Reachable ----
$Ping = Test-Connection -ComputerName $MachineName -Count 2 -Quiet -ErrorAction SilentlyContinue
if (-not $Ping) {
    Write-Log "Machine $MachineName is not reachable." "ERROR"
    Write-Output "FAILED: Machine $MachineName is offline."
    exit 1
}

# ---- Remote Script Block ----
$RemoteScript = {
    param($ScanType)

    $results = @()

    # Windows Defender
    try {
        $DefenderStatus = Get-MpComputerStatus -ErrorAction Stop
        $results += "Windows Defender found. Status: $($DefenderStatus.AMServiceEnabled)"

        # Update definitions
        Update-MpSignature -ErrorAction Stop
        $results += "Windows Defender definitions updated successfully."

        # Trigger scan
        if ($ScanType -eq "full") {
            Start-MpScan -ScanType FullScan -ErrorAction Stop
            $results += "Windows Defender full scan triggered."
        } else {
            Start-MpScan -ScanType QuickScan -ErrorAction Stop
            $results += "Windows Defender quick scan triggered."
        }
    } catch {
        $results += "Windows Defender error: $_"
    }

    # Symantec Endpoint Protection
    try {
        $SymPath = "C:\Program Files (x86)\Symantec\Symantec Endpoint Protection\Smc.exe"
        if (Test-Path $SymPath) {
            & $SymPath -start 2>$null
            Start-Sleep -Seconds 3
            & "C:\Program Files (x86)\Symantec\Symantec Endpoint Protection\DoScan.exe" -mode 201 2>$null
            $results += "Symantec scan triggered."
        }
    } catch {
        $results += "Symantec not found or error: $_"
    }

    # McAfee
    try {
        $McAfeePath = "C:\Program Files\McAfee\Endpoint Security\Threat Prevention\mfetp.exe"
        if (Test-Path $McAfeePath) {
            & $McAfeePath /scan /full 2>$null
            $results += "McAfee scan triggered."
        }
    } catch {
        $results += "McAfee not found or error: $_"
    }

    return $results
}

try {
    $Output = Invoke-Command -ComputerName $MachineName `
                             -ScriptBlock $RemoteScript `
                             -ArgumentList $ScanType `
                             -ErrorAction Stop

    foreach ($line in $Output) {
        Write-Log $line
    }

    Write-Output "SUCCESS: Antivirus definitions updated. $ScanType scan triggered on $MachineName."
    exit 0

} catch {
    Write-Log "Remote execution failed: $_" "ERROR"
    Write-Output "FAILED: Could not update antivirus on $MachineName. Error: $_"
    exit 1
}