param(
    [string]$MachineName,
    [string]$AppName,
    [string]$TicketId,
    [string]$RequesterEmail
)

Write-Host "===== APP INSTALL SCRIPT ====="
Write-Host "Machine    : $MachineName"
Write-Host "App        : $AppName"
Write-Host "Ticket ID  : $TicketId"
Write-Host "Requester  : $RequesterEmail"

$AppName = $AppName.ToLower().Trim()

$AppMap = @{
    "zoom"             = "Zoom.Zoom"
    "microsoft teams"  = "Microsoft.Teams"
    "teams"            = "Microsoft.Teams"
    "chrome"           = "Google.Chrome"
    "google chrome"    = "Google.Chrome"
    "office"           = "Microsoft.Office"
    "ms office"        = "Microsoft.Office"
    "7zip"             = "7zip.7zip"
    "notepad++"        = "Notepad++.Notepad++"
    "vlc"              = "VideoLAN.VLC"
    "anyconnect"       = "Cisco.CiscoAnyConnect"
}

$WingetId = $AppMap[$AppName]

if (-not $WingetId) {
    Write-Host "ERROR: No winget ID found for app '$AppName'"
    exit 1
}

Write-Host "Installing $AppName (winget ID: $WingetId) on $MachineName..."

try {
    $ScriptBlock = {
        param($WingetId, $AppName)
        winget install --id $WingetId --silent --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -eq 0) {
            Write-Host "SUCCESS: $AppName installed."
        } else {
            Write-Host "ERROR: winget exited with code $LASTEXITCODE"
            exit 1
        }
    }

    Invoke-Command -ComputerName $MachineName `
                   -ScriptBlock $ScriptBlock `
                   -ArgumentList $WingetId, $AppName `
                   -ErrorAction Stop

    Write-Host "Installation complete on $MachineName."
    exit 0

} catch {
    Write-Host "ERROR: Failed to connect to $MachineName — $_"
    exit 1
}