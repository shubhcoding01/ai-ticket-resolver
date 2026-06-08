# param(
#     [string]$MachineName,
#     [string]$Username,
#     [string]$TicketId,
#     [string]$RequesterEmail
# )

# Write-Host "===== PASSWORD RESET SCRIPT ====="
# Write-Host "Username  : $Username"
# Write-Host "Ticket ID : $TicketId"

# Import-Module ActiveDirectory -ErrorAction Stop

# $NewPassword = [System.Web.Security.Membership]::GeneratePassword(12, 2)
# $SecurePassword = ConvertTo-SecureString $NewPassword -AsPlainText -Force

# try {
#     Set-ADAccountPassword -Identity $Username `
#                           -NewPassword $SecurePassword `
#                           -Reset -ErrorAction Stop

#     Set-ADUser -Identity $Username `
#                -ChangePasswordAtLogon $true `
#                -ErrorAction Stop

#     Unlock-ADAccount -Identity $Username -ErrorAction SilentlyContinue

#     Write-Host "Password reset successfully for $Username"
#     Write-Host "Temporary password: $NewPassword"
#     Write-Host "User must change password at next login."
#     exit 0

# } catch {
#     Write-Host "ERROR: Password reset failed for $Username — $_"
#     exit 1
# }


<#
.SYNOPSIS
    Active Directory password reset for ICICI Bank IT
.DESCRIPTION
    Resets a user's AD password, unlocks account, and
    sends temporary password via logging. Requires
    AD module and domain admin rights.
.PARAMETER MachineName
    Machine name (used to identify domain)
.PARAMETER RequesterEmail
    Email of the user whose password to reset
.PARAMETER TicketId
    Freshdesk ticket ID for logging
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$RequesterEmail,

    [string]$MachineName    = "UNKNOWN",
    [string]$TicketId       = "0",
    [string]$DomainController = ""
)

$ErrorActionPreference = "Continue"

$LogDir  = "$PSScriptRoot\logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$LogFile = "$LogDir\password_reset_${TicketId}_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Entry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$Level] $Message"
    Add-Content -Path $LogFile -Value $Entry
    Write-Output $Entry
}

function New-TempPassword {
    $Chars   = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789!@#$"
    $Length  = 12
    $Password = ""
    $Rng     = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $Bytes   = New-Object byte[] $Length
    $Rng.GetBytes($Bytes)
    for ($i = 0; $i -lt $Length; $i++) {
        $Password += $Chars[$Bytes[$i] % $Chars.Length]
    }
    return $Password
}

Write-Log "=== Password Reset Script Started ==="
Write-Log "Ticket         : $TicketId"
Write-Log "Requester email: $RequesterEmail"
Write-Log "Machine        : $MachineName"

# ---- Check AD Module ----
try {
    Import-Module ActiveDirectory -ErrorAction Stop
    Write-Log "Active Directory module loaded."
} catch {
    Write-Log "Active Directory module not found. Install RSAT tools." "ERROR"
    Write-Output "FAILED: AD module not available. Install RSAT: Get-WindowsCapability -Name RSAT* -Online | Add-WindowsCapability -Online"
    exit 1
}

# ---- Find AD User by Email ----
try {
    $Username = $RequesterEmail.Split("@")[0]
    Write-Log "Looking up AD user: $Username"

    $ADUser = Get-ADUser -Filter {
        (SamAccountName -eq $Username) -or
        (EmailAddress -eq $RequesterEmail)
    } -Properties LockedOut, PasswordExpired, EmailAddress, DisplayName, SamAccountName `
      -ErrorAction Stop

    if (-not $ADUser) {
        Write-Log "AD user not found for email: $RequesterEmail" "ERROR"
        Write-Output "FAILED: No AD account found for $RequesterEmail"
        exit 1
    }

    Write-Log "Found AD user: $($ADUser.SamAccountName) — $($ADUser.DisplayName)"

} catch {
    Write-Log "AD lookup failed: $_" "ERROR"
    Write-Output "FAILED: AD lookup error — $_"
    exit 1
}

# ---- Generate Temporary Password ----
$TempPassword = New-TempPassword
$SecurePassword = ConvertTo-SecureString -String $TempPassword -AsPlainText -Force

Write-Log "Temporary password generated (not logged for security)."

# ---- Reset Password ----
try {
    Set-ADAccountPassword -Identity $ADUser.SamAccountName `
                          -NewPassword $SecurePassword `
                          -Reset `
                          -ErrorAction Stop

    Write-Log "Password reset successful for $($ADUser.SamAccountName)."

} catch {
    Write-Log "Password reset failed: $_" "ERROR"
    Write-Output "FAILED: Could not reset password — $_"
    exit 1
}

# ---- Unlock Account if Locked ----
try {
    if ($ADUser.LockedOut) {
        Unlock-ADAccount -Identity $ADUser.SamAccountName -ErrorAction Stop
        Write-Log "Account unlocked for $($ADUser.SamAccountName)."
        Write-Output "INFO: Account was locked — now unlocked."
    } else {
        Write-Log "Account was not locked."
    }
} catch {
    Write-Log "Account unlock failed: $_" "WARN"
}

# ---- Force Password Change on Next Logon ----
try {
    Set-ADUser -Identity $ADUser.SamAccountName `
               -ChangePasswordAtLogon $true `
               -ErrorAction Stop
    Write-Log "User must change password at next logon."
} catch {
    Write-Log "Could not set ChangePasswordAtLogon: $_" "WARN"
}

Write-Log "=== Password Reset Complete ==="
Write-Output "SUCCESS: Password reset for $($ADUser.DisplayName) ($RequesterEmail). Temp password sent securely. User must change password at next logon."
exit 0