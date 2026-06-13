<#
.SYNOPSIS
    Remote network adapter and VPN fix for ICICI Bank IT
.DESCRIPTION
    Resets network adapter, flushes DNS, resets TCP/IP stack,
    and attempts VPN reconnection on a remote machine.
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
    [string]$IssueType      = "general"
)

$ErrorActionPreference = "Continue"

$LogDir  = "$PSScriptRoot\logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$LogFile = "$LogDir\network_${TicketId}_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Entry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$Level] $Message"
    Add-Content -Path $LogFile -Value $Entry
    Write-Output $Entry
}

Write-Log "=== Network Fix Script Started ==="
Write-Log "Ticket    : $TicketId"
Write-Log "Machine   : $MachineName"
Write-Log "IssueType : $IssueType"

$Ping = Test-Connection -ComputerName $MachineName -Count 2 -Quiet -ErrorAction SilentlyContinue
if (-not $Ping) {
    Write-Log "Machine $MachineName is not reachable." "ERROR"
    Write-Output "FAILED: Machine $MachineName is offline."
    exit 1
}

$RemoteScript = {
    param($IssueType)
    $results = @()

    # Flush DNS
    ipconfig /flushdns | Out-Null
    $results += "DNS cache flushed."

    # Release and renew IP
    ipconfig /release | Out-Null
    Start-Sleep -Seconds 2
    ipconfig /renew | Out-Null
    $results += "IP address released and renewed."

    # Reset Winsock
    netsh winsock reset | Out-Null
    $results += "Winsock reset complete."

    # Reset TCP/IP
    netsh int ip reset | Out-Null
    $results += "TCP/IP stack reset complete."

    # Disable and re-enable network adapters
    $Adapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" }
    foreach ($Adapter in $Adapters) {
        Disable-NetAdapter -Name $Adapter.Name -Confirm:$false -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Enable-NetAdapter -Name $Adapter.Name -Confirm:$false -ErrorAction SilentlyContinue
        $results += "Network adapter '$($Adapter.Name)' cycled."
    }

    Start-Sleep -Seconds 5

    # Test connectivity
    $PingResult = Test-Connection -ComputerName "8.8.8.8" -Count 2 -Quiet -ErrorAction SilentlyContinue
    if ($PingResult) {
        $results += "Internet connectivity confirmed after reset."
    } else {
        $results += "WARNING: No internet connectivity after reset. May need further investigation."
    }

    # VPN specific fix
    if ($IssueType -eq "vpn") {
        # Restart Cisco AnyConnect service
        $VPNService = Get-Service -Name "vpnagent" -ErrorAction SilentlyContinue
        if ($VPNService) {
            Restart-Service -Name "vpnagent" -Force -ErrorAction SilentlyContinue
            $results += "Cisco AnyConnect VPN service restarted."
        }

        # Clear VPN credential cache
        $VPNCachePath = "$env:APPDATA\Cisco\Cisco AnyConnect Secure Mobility Client"
        if (Test-Path $VPNCachePath) {
            Remove-Item -Path "$VPNCachePath\*.xml" -Force -ErrorAction SilentlyContinue
            $results += "VPN credential cache cleared."
        }
    }

    # Show current IP info
    $IPConfig = Get-NetIPAddress -AddressFamily IPv4 |
                Where-Object { $_.InterfaceAlias -notlike "*Loopback*" } |
                Select-Object InterfaceAlias, IPAddress
    $results += "Current IP: $($IPConfig | ForEach-Object { "$($_.InterfaceAlias): $($_.IPAddress)" } | Out-String)"

    return $results
}

try {
    $Output = Invoke-Command -ComputerName $MachineName `
                             -ScriptBlock $RemoteScript `
                             -ArgumentList $IssueType `
                             -ErrorAction Stop

    foreach ($line in $Output) { Write-Log $line }

    Write-Output "SUCCESS: Network adapter reset complete on $MachineName. DNS flushed and TCP/IP reset."
    exit 0

} catch {
    Write-Log "Remote execution failed: $_" "ERROR"
    Write-Output "FAILED: Network fix failed on $MachineName — $_"
    exit 1
}