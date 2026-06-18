<#
.SYNOPSIS
    Comprehensive system health check for ICICI Bank IT
.DESCRIPTION
    Checks CPU, RAM, Disk, Network, Services, Event Logs,
    Antivirus, Windows Updates and generates a full health report.
    Run before or after any automation script to verify machine state.
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
    [string]$OutputFormat   = "text"
)

$ErrorActionPreference = "Continue"

$LogDir    = "$PSScriptRoot\logs"
$ReportDir = "$PSScriptRoot\reports"
if (-not (Test-Path $LogDir))    { New-Item -ItemType Directory -Path $LogDir    | Out-Null }
if (-not (Test-Path $ReportDir)) { New-Item -ItemType Directory -Path $ReportDir | Out-Null }

$Timestamp  = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile    = "$LogDir\health_${MachineName}_${TicketId}_${Timestamp}.log"
$ReportFile = "$ReportDir\HealthReport_${MachineName}_${Timestamp}.txt"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Entry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$Level] $Message"
    Add-Content -Path $LogFile -Value $Entry
    Write-Output $Entry
}

Write-Log "=== System Health Check Started ==="
Write-Log "Ticket  : $TicketId"
Write-Log "Machine : $MachineName"

# ---- Verify Machine is Reachable ----
$Ping = Test-Connection -ComputerName $MachineName -Count 3 -Quiet -ErrorAction SilentlyContinue
if (-not $Ping) {
    Write-Log "Machine $MachineName is not reachable." "ERROR"
    Write-Output "FAILED: Machine $MachineName is offline or unreachable."
    exit 1
}

Write-Log "Machine $MachineName is reachable. Running health checks..."

# ---- Remote Health Check Script Block ----
$RemoteScript = {

    $Report = @{}
    $Alerts = @()
    $Warnings = @()

    # ==============================================
    # 1. SYSTEM INFORMATION
    # ==============================================
    try {
        $OS      = Get-WmiObject -Class Win32_OperatingSystem
        $CS      = Get-WmiObject -Class Win32_ComputerSystem
        $BIOS    = Get-WmiObject -Class Win32_BIOS
        $CPU     = Get-WmiObject -Class Win32_Processor

        $Report["System"] = @{
            "ComputerName"    = $env:COMPUTERNAME
            "OSName"          = $OS.Caption
            "OSVersion"       = $OS.Version
            "OSBuild"         = $OS.BuildNumber
            "OSArch"          = $OS.OSArchitecture
            "LastBootTime"    = $OS.ConvertToDateTime($OS.LastBootUpTime).ToString("dd MMM yyyy HH:mm:ss")
            "UptimeDays"      = [math]::Round((New-TimeSpan -Start $OS.ConvertToDateTime($OS.LastBootUpTime) -End (Get-Date)).TotalDays, 1)
            "Manufacturer"    = $CS.Manufacturer
            "Model"           = $CS.Model
            "Domain"          = $CS.Domain
            "LoggedOnUser"    = $CS.UserName
            "BIOSVersion"     = $BIOS.SMBIOSBIOSVersion
            "CPUName"         = $CPU.Name
            "CPUCores"        = $CPU.NumberOfCores
            "CPULogical"      = $CPU.NumberOfLogicalProcessors
        }

        $UptimeDays = $Report["System"]["UptimeDays"]
        if ($UptimeDays -gt 30) {
            $Warnings += "Machine has been running for $UptimeDays days without restart."
        }

        Write-Output "[OK] System information collected."
    } catch {
        Write-Output "[WARN] System info collection error: $_"
    }

    # ==============================================
    # 2. CPU USAGE
    # ==============================================
    try {
        $CPULoad = (Get-WmiObject -Class Win32_Processor |
                   Measure-Object -Property LoadPercentage -Average).Average

        $Report["CPU"] = @{
            "CurrentLoadPct" = $CPULoad
            "Status"         = if ($CPULoad -gt 90) { "CRITICAL" } elseif ($CPULoad -gt 70) { "HIGH" } else { "OK" }
        }

        if ($CPULoad -gt 90) {
            $Alerts   += "CRITICAL: CPU usage is at $CPULoad%. Machine may be unresponsive."
        } elseif ($CPULoad -gt 70) {
            $Warnings += "CPU usage is high at $CPULoad%."
        }

        Write-Output "[OK] CPU usage: $CPULoad%"
    } catch {
        Write-Output "[WARN] CPU check error: $_"
    }

    # ==============================================
    # 3. RAM / MEMORY
    # ==============================================
    try {
        $OS       = Get-WmiObject -Class Win32_OperatingSystem
        $TotalRAM = [math]::Round($OS.TotalVisibleMemorySize / 1MB, 2)
        $FreeRAM  = [math]::Round($OS.FreePhysicalMemory     / 1MB, 2)
        $UsedRAM  = [math]::Round($TotalRAM - $FreeRAM, 2)
        $RAMPct   = [math]::Round(($UsedRAM / $TotalRAM) * 100, 1)

        $Report["Memory"] = @{
            "TotalGB"    = $TotalRAM
            "UsedGB"     = $UsedRAM
            "FreeGB"     = $FreeRAM
            "UsedPct"    = $RAMPct
            "Status"     = if ($RAMPct -gt 90) { "CRITICAL" } elseif ($RAMPct -gt 75) { "HIGH" } else { "OK" }
        }

        if ($RAMPct -gt 90) {
            $Alerts   += "CRITICAL: RAM usage is at $RAMPct% ($UsedRAM GB of $TotalRAM GB used)."
        } elseif ($RAMPct -gt 75) {
            $Warnings += "RAM usage is high at $RAMPct%."
        }

        Write-Output "[OK] RAM: $UsedRAM GB used / $TotalRAM GB total ($RAMPct%)"
    } catch {
        Write-Output "[WARN] Memory check error: $_"
    }

    # ==============================================
    # 4. DISK SPACE
    # ==============================================
    try {
        $Disks = Get-WmiObject -Class Win32_LogicalDisk -Filter "DriveType=3"
        $DiskReport = @()

        foreach ($Disk in $Disks) {
            $TotalGB = [math]::Round($Disk.Size       / 1GB, 2)
            $FreeGB  = [math]::Round($Disk.FreeSpace  / 1GB, 2)
            $UsedPct = [math]::Round((1 - $Disk.FreeSpace / $Disk.Size) * 100, 1)

            $Status = if ($UsedPct -gt 95) { "CRITICAL" } `
                      elseif ($UsedPct -gt 85) { "WARNING" } `
                      else { "OK" }

            $DiskReport += @{
                "Drive"   = $Disk.DeviceID
                "TotalGB" = $TotalGB
                "FreeGB"  = $FreeGB
                "UsedPct" = $UsedPct
                "Status"  = $Status
            }

            if ($UsedPct -gt 95) {
                $Alerts   += "CRITICAL: Drive $($Disk.DeviceID) is $UsedPct% full ($FreeGB GB free)."
            } elseif ($UsedPct -gt 85) {
                $Warnings += "Drive $($Disk.DeviceID) is $UsedPct% full ($FreeGB GB free)."
            }

            Write-Output "[OK] Disk $($Disk.DeviceID): $FreeGB GB free / $TotalGB GB total ($UsedPct% used) [$Status]"
        }

        $Report["Disks"] = $DiskReport
    } catch {
        Write-Output "[WARN] Disk check error: $_"
    }

    # ==============================================
    # 5. NETWORK CONNECTIVITY
    # ==============================================
    try {
        $NetAdapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" }
        $NetReport   = @()

        foreach ($Adapter in $NetAdapters) {
            $IPConfig = Get-NetIPAddress -InterfaceIndex $Adapter.ifIndex `
                                         -AddressFamily IPv4 `
                                         -ErrorAction SilentlyContinue

            $NetReport += @{
                "Name"       = $Adapter.Name
                "Status"     = $Adapter.Status
                "Speed"      = "$([math]::Round($Adapter.LinkSpeed / 1MB, 0)) Mbps"
                "IPAddress"  = ($IPConfig | Select-Object -First 1).IPAddress
                "MACAddress" = $Adapter.MacAddress
            }
        }

        $Report["Network"] = $NetReport

        # Test internet connectivity
        $InternetTest = Test-Connection -ComputerName "8.8.8.8" -Count 2 -Quiet -ErrorAction SilentlyContinue
        $Report["InternetConnected"] = $InternetTest

        if (-not $InternetTest) {
            $Alerts += "CRITICAL: No internet connectivity detected."
        }

        # Test DNS resolution
        try {
            $DNS = Resolve-DnsName -Name "google.com" -ErrorAction Stop
            $Report["DNSWorking"] = $true
            Write-Output "[OK] DNS resolution working."
        } catch {
            $Report["DNSWorking"] = $false
            $Alerts += "DNS resolution failed. Check network/DNS settings."
        }

        Write-Output "[OK] Network adapters: $($NetAdapters.Count) active"
        Write-Output "[OK] Internet: $(if ($InternetTest) { 'Connected' } else { 'NOT CONNECTED' })"
    } catch {
        Write-Output "[WARN] Network check error: $_"
    }

    # ==============================================
    # 6. CRITICAL WINDOWS SERVICES
    # ==============================================
    try {
        $CriticalServices = @(
            "wuauserv",        # Windows Update
            "WinDefend",       # Windows Defender
            "Spooler",         # Print Spooler
            "BITS",            # Background Intelligent Transfer
            "Dnscache",        # DNS Client
            "LanmanWorkstation", # Workstation (network drives)
            "wlan autoconfig", # WiFi
            "EventLog",        # Event Log
            "Schedule",        # Task Scheduler
            "RpcSs",           # Remote Procedure Call
            "w32tm",           # Windows Time
            "AudioSrv"         # Windows Audio
        )

        $ServiceReport = @()

        foreach ($SvcName in $CriticalServices) {
            $Svc = Get-Service -Name $SvcName -ErrorAction SilentlyContinue
            if ($Svc) {
                $ServiceReport += @{
                    "Name"        = $Svc.DisplayName
                    "ServiceName" = $Svc.Name
                    "Status"      = $Svc.Status.ToString()
                    "StartType"   = $Svc.StartType.ToString()
                }

                if ($Svc.Status -ne "Running" -and $Svc.StartType -ne "Disabled") {
                    $Warnings += "Service '$($Svc.DisplayName)' is $($Svc.Status) (expected Running)."
                }
            }
        }

        $Report["Services"] = $ServiceReport
        $StoppedCount = ($ServiceReport | Where-Object { $_["Status"] -ne "Running" }).Count
        Write-Output "[OK] Services checked: $($ServiceReport.Count) — $StoppedCount unexpected stops"
    } catch {
        Write-Output "[WARN] Service check error: $_"
    }

    # ==============================================
    # 7. WINDOWS DEFENDER / ANTIVIRUS STATUS
    # ==============================================
    try {
        $DefenderStatus = Get-MpComputerStatus -ErrorAction Stop

        $DefDaysOld = [math]::Round(
            (New-TimeSpan -Start $DefenderStatus.AntivirusSignatureLastUpdated -End (Get-Date)).TotalDays,
            1
        )

        $Report["Antivirus"] = @{
            "DefenderEnabled"       = $DefenderStatus.AntivirusEnabled
            "RealTimeProtection"    = $DefenderStatus.RealTimeProtectionEnabled
            "DefinitionAge"         = "$DefDaysOld days"
            "LastQuickScan"         = $DefenderStatus.QuickScanAge
            "LastFullScan"          = $DefenderStatus.FullScanAge
            "ThreatStatus"          = $DefenderStatus.AMRunningMode
        }

        if (-not $DefenderStatus.RealTimeProtectionEnabled) {
            $Alerts += "CRITICAL: Windows Defender Real-Time Protection is DISABLED."
        }

        if ($DefDaysOld -gt 3) {
            $Warnings += "Antivirus definitions are $DefDaysOld days old. Update recommended."
        }

        if ($DefenderStatus.QuickScanAge -gt 7) {
            $Warnings += "No quick scan in $($DefenderStatus.QuickScanAge) days."
        }

        Write-Output "[OK] Defender: RealTime=$($DefenderStatus.RealTimeProtectionEnabled) | Defs: $DefDaysOld days old"
    } catch {
        Write-Output "[INFO] Windows Defender check: $_ (may have 3rd party AV)"
        $Report["Antivirus"] = @{ "Status" = "Windows Defender not primary AV or access denied" }
    }

    # ==============================================
    # 8. PENDING WINDOWS UPDATES
    # ==============================================
    try {
        $UpdateSession  = New-Object -ComObject Microsoft.Update.Session
        $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
        $SearchResult   = $UpdateSearcher.Search("IsInstalled=0 and Type='Software'")
        $PendingCount   = $SearchResult.Updates.Count

        $Report["WindowsUpdates"] = @{
            "PendingCount" = $PendingCount
            "Status"       = if ($PendingCount -gt 10) { "CRITICAL" } elseif ($PendingCount -gt 0) { "PENDING" } else { "UP_TO_DATE" }
        }

        if ($PendingCount -gt 10) {
            $Warnings += "$PendingCount Windows updates pending. Recommend scheduling update."
        }

        Write-Output "[OK] Windows Updates: $PendingCount pending"
    } catch {
        Write-Output "[WARN] Windows Update check error: $_"
        $Report["WindowsUpdates"] = @{ "Status" = "Check failed" }
    }

    # ==============================================
    # 9. RECENT CRITICAL EVENT LOG ERRORS
    # ==============================================
    try {
        $Since         = (Get-Date).AddHours(-24)
        $CriticalEvents = Get-EventLog -LogName System -EntryType Error -After $Since `
                                        -ErrorAction SilentlyContinue |
                         Select-Object -First 10

        $AppErrors     = Get-EventLog -LogName Application -EntryType Error -After $Since `
                                       -ErrorAction SilentlyContinue |
                        Select-Object -First 5

        $EventCount    = ($CriticalEvents.Count + $AppErrors.Count)

        $Report["RecentErrors"] = @{
            "SystemErrors"      = $CriticalEvents.Count
            "ApplicationErrors" = $AppErrors.Count
            "TotalLast24Hours"  = $EventCount
        }

        if ($EventCount -gt 20) {
            $Warnings += "$EventCount errors in Event Log in last 24 hours. Check logs."
        }

        Write-Output "[OK] Event Log errors (24h): System=$($CriticalEvents.Count) App=$($AppErrors.Count)"
    } catch {
        Write-Output "[WARN] Event Log check error: $_"
    }

    # ==============================================
    # 10. STARTUP PROGRAMS (slow boot indicators)
    # ==============================================
    try {
        $StartupItems = Get-CimInstance -ClassName Win32_StartupCommand |
                        Select-Object Name, Command, Location

        $Report["StartupItems"] = @{
            "Count" = $StartupItems.Count
            "Items" = ($StartupItems | ForEach-Object { $_.Name }) -join ", "
        }

        if ($StartupItems.Count -gt 15) {
            $Warnings += "$($StartupItems.Count) startup programs detected. May slow boot time."
        }

        Write-Output "[OK] Startup programs: $($StartupItems.Count)"
    } catch {
        Write-Output "[WARN] Startup check error: $_"
    }

    # ==============================================
    # 11. BATTERY STATUS (laptops)
    # ==============================================
    try {
        $Battery = Get-WmiObject -Class Win32_Battery -ErrorAction SilentlyContinue
        if ($Battery) {
            $BatteryPct = $Battery.EstimatedChargeRemaining
            $BatteryStatus = switch ($Battery.BatteryStatus) {
                1 { "Discharging" }
                2 { "AC Connected" }
                3 { "Fully Charged" }
                4 { "Low" }
                5 { "Critical" }
                default { "Unknown" }
            }

            $Report["Battery"] = @{
                "ChargePercent" = $BatteryPct
                "Status"        = $BatteryStatus
            }

            if ($BatteryPct -lt 20) {
                $Alerts += "Battery charge is at $BatteryPct% ($BatteryStatus)."
            }

            Write-Output "[OK] Battery: $BatteryPct% — $BatteryStatus"
        } else {
            $Report["Battery"] = @{ "Status" = "No battery (desktop)" }
        }
    } catch {
        Write-Output "[INFO] Battery check skipped."
    }

    # ==============================================
    # 12. TOP RESOURCE-CONSUMING PROCESSES
    # ==============================================
    try {
        $TopCPU = Get-Process | Sort-Object CPU -Descending |
                  Select-Object -First 5 Name,
                  @{N="CPU_s"; E={[math]::Round($_.CPU, 1)}},
                  @{N="RAM_MB"; E={[math]::Round($_.WorkingSet64 / 1MB, 1)}}

        $Report["TopProcesses"] = ($TopCPU | ForEach-Object {
            "$($_.Name) (CPU:$($_.CPU_s)s RAM:$($_.RAM_MB)MB)"
        }) -join " | "

        Write-Output "[OK] Top processes collected."
    } catch {
        Write-Output "[WARN] Process check error: $_"
    }

    # ==============================================
    # BUILD FINAL HEALTH SCORE
    # ==============================================
    $HealthScore = 100
    $HealthScore -= ($Alerts.Count   * 20)
    $HealthScore -= ($Warnings.Count * 5)
    $HealthScore  = [math]::Max(0, $HealthScore)

    $HealthStatus = if ($HealthScore -ge 80) { "HEALTHY" } `
                    elseif ($HealthScore -ge 60) { "FAIR" } `
                    elseif ($HealthScore -ge 40) { "POOR" } `
                    else { "CRITICAL" }

    $Report["HealthScore"]  = $HealthScore
    $Report["HealthStatus"] = $HealthStatus
    $Report["Alerts"]       = $Alerts
    $Report["Warnings"]     = $Warnings
    $Report["CheckTime"]    = (Get-Date -Format "dd MMM yyyy HH:mm:ss")

    return $Report
}

# ---- Execute Remote Check ----
try {
    $HealthData = Invoke-Command -ComputerName $MachineName `
                                 -ScriptBlock $RemoteScript `
                                 -ErrorAction Stop

    Write-Log "Health check completed for $MachineName."

    # ---- Build Text Report ----
    $ReportLines = @()
    $ReportLines += "==========================================================="
    $ReportLines += "ICICI Bank — System Health Report"
    $ReportLines += "==========================================================="
    $ReportLines += "Machine      : $MachineName"
    $ReportLines += "Ticket       : $TicketId"
    $ReportLines += "Check Time   : $($HealthData.CheckTime)"
    $ReportLines += "Health Score : $($HealthData.HealthScore)/100"
    $ReportLines += "Health Status: $($HealthData.HealthStatus)"
    $ReportLines += "==========================================================="

    if ($HealthData.Alerts.Count -gt 0) {
        $ReportLines += ""
        $ReportLines += "CRITICAL ALERTS ($($HealthData.Alerts.Count)):"
        $ReportLines += "-----------------------------------------------------------"
        foreach ($Alert in $HealthData.Alerts) {
            $ReportLines += "  [!] $Alert"
        }
    }

    if ($HealthData.Warnings.Count -gt 0) {
        $ReportLines += ""
        $ReportLines += "WARNINGS ($($HealthData.Warnings.Count)):"
        $ReportLines += "-----------------------------------------------------------"
        foreach ($Warning in $HealthData.Warnings) {
            $ReportLines += "  [W] $Warning"
        }
    }

    $ReportLines += ""
    $ReportLines += "SYSTEM DETAILS:"
    $ReportLines += "-----------------------------------------------------------"

    if ($HealthData.System) {
        $ReportLines += "  OS          : $($HealthData.System.OSName) (Build $($HealthData.System.OSBuild))"
        $ReportLines += "  Model       : $($HealthData.System.Manufacturer) $($HealthData.System.Model)"
        $ReportLines += "  CPU         : $($HealthData.System.CPUName)"
        $ReportLines += "  Uptime      : $($HealthData.System.UptimeDays) days (since $($HealthData.System.LastBootTime))"
        $ReportLines += "  Domain      : $($HealthData.System.Domain)"
        $ReportLines += "  Logged on   : $($HealthData.System.LoggedOnUser)"
    }

    if ($HealthData.CPU) {
        $ReportLines += "  CPU Load    : $($HealthData.CPU.CurrentLoadPct)% [$($HealthData.CPU.Status)]"
    }

    if ($HealthData.Memory) {
        $ReportLines += "  RAM         : $($HealthData.Memory.UsedGB) GB / $($HealthData.Memory.TotalGB) GB ($($HealthData.Memory.UsedPct)%) [$($HealthData.Memory.Status)]"
    }

    if ($HealthData.Disks) {
        foreach ($Disk in $HealthData.Disks) {
            $ReportLines += "  Disk $($Disk.Drive)      : $($Disk.FreeGB) GB free / $($Disk.TotalGB) GB ($($Disk.UsedPct)% used) [$($Disk.Status)]"
        }
    }

    if ($HealthData.InternetConnected -ne $null) {
        $ReportLines += "  Internet    : $(if ($HealthData.InternetConnected) { 'Connected' } else { 'DISCONNECTED' })"
        $ReportLines += "  DNS         : $(if ($HealthData.DNSWorking) { 'Working' } else { 'FAILED' })"
    }

    if ($HealthData.Antivirus) {
        $ReportLines += "  Antivirus   : Defs=$($HealthData.Antivirus.DefinitionAge) | RealTime=$($HealthData.Antivirus.RealTimeProtection)"
    }

    if ($HealthData.WindowsUpdates) {
        $ReportLines += "  Updates     : $($HealthData.WindowsUpdates.PendingCount) pending [$($HealthData.WindowsUpdates.Status)]"
    }

    if ($HealthData.RecentErrors) {
        $ReportLines += "  Events(24h) : $($HealthData.RecentErrors.TotalLast24Hours) errors (Sys=$($HealthData.RecentErrors.SystemErrors) App=$($HealthData.RecentErrors.ApplicationErrors))"
    }

    if ($HealthData.Battery) {
        $ReportLines += "  Battery     : $($HealthData.Battery.Status)"
    }

    if ($HealthData.TopProcesses) {
        $ReportLines += ""
        $ReportLines += "  Top Processes: $($HealthData.TopProcesses)"
    }

    $ReportLines += ""
    $ReportLines += "==========================================================="
    $ReportLines += "Full log: $LogFile"
    $ReportLines += "==========================================================="

    # Save report
    $ReportLines | Out-File -FilePath $ReportFile -Encoding UTF8
    foreach ($line in $ReportLines) { Write-Log $line }

    Write-Output "SUCCESS: Health check complete. Score=$($HealthData.HealthScore)/100 Status=$($HealthData.HealthStatus)"
    Write-Output "Report saved to: $ReportFile"

    # Return exit code based on health
    if ($HealthData.HealthStatus -eq "CRITICAL") { exit 2 }
    elseif ($HealthData.HealthStatus -eq "POOR")  { exit 1 }
    else { exit 0 }

} catch {
    Write-Log "Remote health check failed: $_" "ERROR"
    Write-Output "FAILED: Health check failed on $MachineName — $_"
    exit 1
}