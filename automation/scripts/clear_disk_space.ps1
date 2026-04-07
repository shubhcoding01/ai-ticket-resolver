param(
    [string]$MachineName,
    [string]$Action = "repair",
    [string]$TicketId,
    [string]$RequesterEmail
)

Write-Host "===== OS REPAIR / DISK CLEANUP SCRIPT ====="
Write-Host "Machine   : $MachineName"
Write-Host "Action    : $Action"
Write-Host "Ticket ID : $TicketId"

try {
    $ScriptBlock = {
        Write-Host "Running System File Checker (sfc /scannow)..."
        sfc /scannow

        Write-Host "Running DISM health restore..."
        DISM /Online /Cleanup-Image /RestoreHealth

        Write-Host "Cleaning temp files..."
        Remove-Item -Path "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item -Path "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue

        $Drive = Get-PSDrive C
        $FreeGB = [math]::Round($Drive.Free / 1GB, 2)
        Write-Host "Free disk space on C: $FreeGB GB"

        Write-Host "OS repair and cleanup complete."
    }

    Invoke-Command -ComputerName $MachineName `
                   -ScriptBlock $ScriptBlock `
                   -ErrorAction Stop

    exit 0

} catch {
    Write-Host "ERROR: Failed on $MachineName — $_"
    exit 1
}