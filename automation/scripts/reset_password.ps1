param(
    [string]$MachineName,
    [string]$Username,
    [string]$TicketId,
    [string]$RequesterEmail
)

Write-Host "===== PASSWORD RESET SCRIPT ====="
Write-Host "Username  : $Username"
Write-Host "Ticket ID : $TicketId"

Import-Module ActiveDirectory -ErrorAction Stop

$NewPassword = [System.Web.Security.Membership]::GeneratePassword(12, 2)
$SecurePassword = ConvertTo-SecureString $NewPassword -AsPlainText -Force

try {
    Set-ADAccountPassword -Identity $Username `
                          -NewPassword $SecurePassword `
                          -Reset -ErrorAction Stop

    Set-ADUser -Identity $Username `
               -ChangePasswordAtLogon $true `
               -ErrorAction Stop

    Unlock-ADAccount -Identity $Username -ErrorAction SilentlyContinue

    Write-Host "Password reset successfully for $Username"
    Write-Host "Temporary password: $NewPassword"
    Write-Host "User must change password at next login."
    exit 0

} catch {
    Write-Host "ERROR: Password reset failed for $Username — $_"
    exit 1
}