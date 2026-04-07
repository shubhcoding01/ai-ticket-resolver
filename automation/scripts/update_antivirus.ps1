param(
    [string]$MachineName,
    [string]$ScanType = "full",
    [string]$TicketId,
    [string]$RequesterEmail
)

Write-Host "===== ANTIVIRUS UPDATE SCRIPT ====="
Write-Host "Machine   : $MachineName"
Write-Host "Scan Type : $ScanType"
Write-Host "Ticket ID : $TicketId"

try {
    $ScriptBlock = {
        param($ScanType)

        Write-Host "Updating Windows Defender definitions..."
        Update-MpSignature -ErrorAction Stop
        Write-Host "Definitions updated successfully."

        if ($ScanType -eq "full") {
            Write-Host "Starting full antivirus scan..."
            Start-MpScan -ScanType FullScan -ErrorAction Stop
        } else {
            Write-Host "Starting quick antivirus scan..."
            Start-MpScan -ScanType QuickScan -ErrorAction Stop
        }

        $Status = Get-MpComputerStatus
        Write-Host "AV Status     : $($Status.AMRunningMode)"
        Write-Host "Last Updated  : $($Status.AntivirusSignatureLastUpdated)"
        Write-Host "Real-time     : $($Status.RealTimeProtectionEnabled)"
    }

    Invoke-Command -ComputerName $MachineName `
                   -ScriptBlock $ScriptBlock `
                   -ArgumentList $ScanType `
                   -ErrorAction Stop

    Write-Host "Antivirus update and scan complete on $MachineName."
    exit 0

} catch {
    Write-Host "ERROR: Failed on $MachineName — $_"
    exit 1
}