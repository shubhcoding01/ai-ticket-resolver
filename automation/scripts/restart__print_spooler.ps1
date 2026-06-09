# param(
#     [string]$MachineName,
#     [string]$Action = "restart_spooler",
#     [string]$TicketId,
#     [string]$RequesterEmail
# )

# Write-Host "===== PRINTER FIX SCRIPT ====="
# Write-Host "Machine   : $MachineName"
# Write-Host "Ticket ID : $TicketId"

# try {
#     $ScriptBlock = {
#         Write-Host "Stopping Print Spooler service..."
#         Stop-Service -Name Spooler -Force

#         Write-Host "Clearing print queue..."
#         Remove-Item -Path "C:\Windows\System32\spool\PRINTERS\*" `
#                     -Recurse -Force -ErrorAction SilentlyContinue

#         Write-Host "Starting Print Spooler service..."
#         Start-Service -Name Spooler

#         $Status = Get-Service -Name Spooler
#         Write-Host "Print Spooler status: $($Status.Status)"

#         if ($Status.Status -eq "Running") {
#             Write-Host "SUCCESS: Print Spooler restarted."
#         } else {
#             Write-Host "ERROR: Print Spooler failed to start."
#             exit 1
#         }
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
    Remote print spooler restart and queue clear for ICICI Bank IT
.DESCRIPTION
    Restarts the Print Spooler service, clears stuck print jobs,
    and reinstalls default network printer if needed.
.PARAMETER MachineName
    Target machine name
.PARAMETER TicketId
    Freshdesk ticket ID for logging
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$MachineName,

    [string]$TicketId       = "0",
    [string]$RequesterEmail = "",
    [string]$PrinterName    = ""
)

$ErrorActionPreference = "Continue"

$LogDir  = "$PSScriptRoot\logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$LogFile = "$LogDir\printer_${TicketId}_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Entry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$Level] $Message"
    Add-Content -Path $LogFile -Value $Entry
    Write-Output $Entry
}

Write-Log "=== Print Spooler Restart Script Started ==="
Write-Log "Ticket  : $TicketId"
Write-Log "Machine : $MachineName"
Write-Log "Printer : $PrinterName"

# ---- Verify Machine ----
$Ping = Test-Connection -ComputerName $MachineName -Count 2 -Quiet -ErrorAction SilentlyContinue
if (-not $Ping) {
    Write-Log "Machine $MachineName is not reachable." "ERROR"
    Write-Output "FAILED: Machine $MachineName is offline."
    exit 1
}

$RemoteScript = {
    param($PrinterName)

    $results = @()

    try {
        # Stop Print Spooler
        Stop-Service -Name Spooler -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        $results += "Print Spooler service stopped."

        # Clear print queue
        $SpoolPath = "C:\Windows\System32\spool\PRINTERS"
        $Files     = Get-ChildItem -Path $SpoolPath -ErrorAction SilentlyContinue
        if ($Files.Count -gt 0) {
            Remove-Item -Path "$SpoolPath\*" -Force -ErrorAction SilentlyContinue
            $results += "Cleared $($Files.Count) stuck print job(s)."
        } else {
            $results += "No stuck print jobs found."
        }

        # Restart Print Spooler
        Start-Service -Name Spooler -ErrorAction Stop
        Start-Sleep -Seconds 2
        $results += "Print Spooler service restarted successfully."

        # Verify service is running
        $Status = (Get-Service -Name Spooler).Status
        $results += "Print Spooler status: $Status"

        # Set spooler to auto-start
        Set-Service -Name Spooler -StartupType Automatic
        $results += "Print Spooler set to automatic startup."

        # List available printers
        $Printers = Get-Printer -ErrorAction SilentlyContinue
        $results += "Available printers: $($Printers.Name -join ', ')"

        # Set default printer if specified
        if ($PrinterName -ne "") {
            $Match = $Printers | Where-Object { $_.Name -like "*$PrinterName*" }
            if ($Match) {
                $Match[0] | Set-Printer -Shared $true -ErrorAction SilentlyContinue
                $results += "Default printer updated: $($Match[0].Name)"
            }
        }

    } catch {
        $results += "Error: $_"
    }

    return $results
}

try {
    $Output = Invoke-Command -ComputerName $MachineName `
                             -ScriptBlock $RemoteScript `
                             -ArgumentList $PrinterName `
                             -ErrorAction Stop

    foreach ($line in $Output) { Write-Log $line }

    Write-Output "SUCCESS: Print Spooler restarted and queue cleared on $MachineName."
    exit 0

} catch {
    Write-Log "Remote execution failed: $_" "ERROR"
    Write-Output "FAILED: Could not restart Print Spooler on $MachineName — $_"
    exit 1
}