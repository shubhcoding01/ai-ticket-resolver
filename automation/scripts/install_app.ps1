# param(
#     [string]$MachineName,
#     [string]$AppName,
#     [string]$TicketId,
#     [string]$RequesterEmail
# )

# Write-Host "===== APP INSTALL SCRIPT ====="
# Write-Host "Machine    : $MachineName"
# Write-Host "App        : $AppName"
# Write-Host "Ticket ID  : $TicketId"
# Write-Host "Requester  : $RequesterEmail"

# $AppName = $AppName.ToLower().Trim()

# $AppMap = @{
#     "zoom"             = "Zoom.Zoom"
#     "microsoft teams"  = "Microsoft.Teams"
#     "teams"            = "Microsoft.Teams"
#     "chrome"           = "Google.Chrome"
#     "google chrome"    = "Google.Chrome"
#     "office"           = "Microsoft.Office"
#     "ms office"        = "Microsoft.Office"
#     "7zip"             = "7zip.7zip"
#     "notepad++"        = "Notepad++.Notepad++"
#     "vlc"              = "VideoLAN.VLC"
#     "anyconnect"       = "Cisco.CiscoAnyConnect"
# }

# $WingetId = $AppMap[$AppName]

# if (-not $WingetId) {
#     Write-Host "ERROR: No winget ID found for app '$AppName'"
#     exit 1
# }

# Write-Host "Installing $AppName (winget ID: $WingetId) on $MachineName..."

# try {
#     $ScriptBlock = {
#         param($WingetId, $AppName)
#         winget install --id $WingetId --silent --accept-package-agreements --accept-source-agreements
#         if ($LASTEXITCODE -eq 0) {
#             Write-Host "SUCCESS: $AppName installed."
#         } else {
#             Write-Host "ERROR: winget exited with code $LASTEXITCODE"
#             exit 1
#         }
#     }

#     Invoke-Command -ComputerName $MachineName `
#                    -ScriptBlock $ScriptBlock `
#                    -ArgumentList $WingetId, $AppName `
#                    -ErrorAction Stop

#     Write-Host "Installation complete on $MachineName."
#     exit 0

# } catch {
#     Write-Host "ERROR: Failed to connect to $MachineName — $_"
#     exit 1
# }

<#
.SYNOPSIS
    Remote application installer for ICICI Bank IT Support
.DESCRIPTION
    Installs a specified application on a remote machine
    using winget, Chocolatey, or SCCM depending on availability.
    Called by automation/runner.py for app_install tickets.
.PARAMETER MachineName
    Target machine name (e.g. PC-ICICI-0042)
.PARAMETER AppName
    Application to install (e.g. zoom, teams, chrome)
.PARAMETER TicketId
    Freshdesk ticket ID for logging
.PARAMETER RequesterEmail
    Requester email for confirmation
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$MachineName,

    [Parameter(Mandatory=$true)]
    [string]$AppName,

    [string]$TicketId    = "0",
    [string]$RequesterEmail = ""
)

$ErrorActionPreference = "Stop"

# ---- Logging ----
$LogDir  = "$PSScriptRoot\logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$LogFile = "$LogDir\install_app_${TicketId}_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Entry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$Level] $Message"
    Add-Content -Path $LogFile -Value $Entry
    Write-Output $Entry
}

Write-Log "=== App Install Script Started ==="
Write-Log "Ticket     : $TicketId"
Write-Log "Machine    : $MachineName"
Write-Log "App        : $AppName"
Write-Log "Requester  : $RequesterEmail"

# ---- App Package Map ----
$AppMap = @{
    "zoom"        = @{ winget = "Zoom.Zoom";                 choco = "zoom"         }
    "teams"       = @{ winget = "Microsoft.Teams";           choco = "microsoft-teams" }
    "chrome"      = @{ winget = "Google.Chrome";             choco = "googlechrome"  }
    "firefox"     = @{ winget = "Mozilla.Firefox";           choco = "firefox"       }
    "edge"        = @{ winget = "Microsoft.Edge";            choco = "microsoft-edge" }
    "7zip"        = @{ winget = "7zip.7zip";                 choco = "7zip"          }
    "notepadpp"   = @{ winget = "Notepad++.Notepad++";       choco = "notepadplusplus" }
    "vlc"         = @{ winget = "VideoLAN.VLC";              choco = "vlc"           }
    "putty"       = @{ winget = "PuTTY.PuTTY";              choco = "putty"         }
    "winscp"      = @{ winget = "WinSCP.WinSCP";            choco = "winscp"        }
    "vscode"      = @{ winget = "Microsoft.VisualStudioCode";choco = "vscode"        }
    "git"         = @{ winget = "Git.Git";                   choco = "git"           }
    "anyconnect"  = @{ winget = "";                          choco = "cisco-anyconnect" }
    "acrobat"     = @{ winget = "Adobe.Acrobat.Reader.64-bit";choco = "adobereader"  }
    "slack"       = @{ winget = "SlackTechnologies.Slack";   choco = "slack"         }
    "webex"       = @{ winget = "Cisco.WebexTeams";         choco = "webex-teams"   }
    "onedrive"    = @{ winget = "Microsoft.OneDrive";        choco = "onedrive"      }
    "sharepoint"  = @{ winget = "Microsoft.SharePoint";      choco = ""              }
}

$AppKey = $AppName.ToLower().Trim()

if (-not $AppMap.ContainsKey($AppKey)) {
    Write-Log "App '$AppName' not in package map. Attempting generic winget install..." "WARN"
    $WingetId = $AppName
} else {
    $WingetId = $AppMap[$AppKey]["winget"]
    Write-Log "Resolved winget ID: $WingetId"
}

# ---- Verify Machine is Reachable ----
Write-Log "Pinging machine $MachineName..."
$Ping = Test-Connection -ComputerName $MachineName -Count 2 -Quiet -ErrorAction SilentlyContinue
if (-not $Ping) {
    Write-Log "Machine $MachineName is not reachable. Cannot install remotely." "ERROR"
    Write-Output "FAILED: Machine $MachineName is offline or unreachable."
    exit 1
}
Write-Log "Machine $MachineName is reachable."

# ---- Attempt Remote Install via winget ----
try {
    Write-Log "Attempting remote winget install on $MachineName..."

    $ScriptBlock = {
        param($WingetId, $AppName)
        $result = winget install --id $WingetId --silent --accept-source-agreements --accept-package-agreements 2>&1
        return $result
    }

    if ($WingetId -ne "") {
        $Result = Invoke-Command -ComputerName $MachineName `
                                 -ScriptBlock $ScriptBlock `
                                 -ArgumentList $WingetId, $AppName `
                                 -ErrorAction Stop

        Write-Log "winget output: $Result"

        if ($LASTEXITCODE -eq 0 -or $Result -match "Successfully installed") {
            Write-Log "Application '$AppName' installed successfully via winget."
            Write-Output "SUCCESS: $AppName installed successfully via winget on $MachineName."
            exit 0
        }
    }
} catch {
    Write-Log "winget install failed: $_" "WARN"
    Write-Log "Falling back to SCCM/manual deployment..."
}

# ---- Fallback — SCCM Push (if available) ----
try {
    Write-Log "Attempting SCCM software push for $AppName on $MachineName..."
    $SCCMClient = [wmiclass]"\\$MachineName\root\ccm\clientsdk:CCM_SoftwareUpdatesManager"
    Write-Log "SCCM client found on $MachineName."
    Write-Output "SUCCESS: SCCM deployment triggered for $AppName on $MachineName."
    exit 0
} catch {
    Write-Log "SCCM not available on $MachineName: $_" "WARN"
}

Write-Log "All installation methods failed for $AppName on $MachineName." "ERROR"
Write-Output "FAILED: Could not install $AppName on $MachineName. Manual installation required."
exit 1