param(
    [string]$MachineName,
    [string]$Action = "restart_spooler",
    [string]$TicketId,
    [string]$RequesterEmail
)

Write-Host "===== PRINTER FIX SCRIPT ====="
Write-Host "Machine   : $MachineName"
Write-Host "Ticket ID : $TicketId"

try {
    $ScriptBlock = {
        Write-Host "Stopping Print Spooler service..."
        Stop-Service -Name Spooler -Force

        Write-Host "Clearing print queue..."
        Remove-Item -Path "C:\Windows\System32\spool\PRINTERS\*" `
                    -Recurse -Force -ErrorAction SilentlyContinue

        Write-Host "Starting Print Spooler service..."
        Start-Service -Name Spooler

        $Status = Get-Service -Name Spooler
        Write-Host "Print Spooler status: $($Status.Status)"

        if ($Status.Status -eq "Running") {
            Write-Host "SUCCESS: Print Spooler restarted."
        } else {
            Write-Host "ERROR: Print Spooler failed to start."
            exit 1
        }
    }

    Invoke-Command -ComputerName $MachineName `
                   -ScriptBlock $ScriptBlock `
                   -ErrorAction Stop

    exit 0

} catch {
    Write-Host "ERROR: Failed on $MachineName — $_"
    exit 1
}