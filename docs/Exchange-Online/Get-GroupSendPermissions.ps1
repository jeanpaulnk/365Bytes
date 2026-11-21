<#
.SYNOPSIS
    Lists DLs, DDLs and Microsoft 365 groups on which a user has
    Send As or Send on Behalf permission in Exchange Online.
.EXAMPLE
    .\Get-GroupSendPermissions.ps1 -User user@domain.com
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$User
)

if (-not (Get-Command Get-RecipientPermission -ErrorAction SilentlyContinue)) {
    throw "Not connected. Run Connect-ExchangeOnline first."
}

$trustee = Get-Recipient -Identity $User -ErrorAction Stop
# Values GrantSendOnBehalfTo may hold for this user
$ids = @($trustee.Name, $trustee.DisplayName, $trustee.Alias,
         $trustee.DistinguishedName, $trustee.Identity.ToString(),
         $trustee.PrimarySmtpAddress.ToString()) | Where-Object { $_ } | Select-Object -Unique

$typeMap = @{
    MailUniversalDistributionGroup = 'DL'
    MailUniversalSecurityGroup     = 'DL'
    MailNonUniversalGroup          = 'DL'
    RoomList                       = 'DL'
    DynamicDistributionGroup       = 'DDL'
    GroupMailbox                   = 'M365Group'
}

$results = [System.Collections.Generic.List[object]]::new()

# --- Send As (one call covers DLs, DDLs and M365 groups) ---
Write-Verbose "Checking Send As..."
$sendAs = Get-RecipientPermission -Trustee $trustee.Identity -AccessRights SendAs -ResultSize Unlimited
foreach ($p in $sendAs) {
    $r = Get-Recipient -Identity $p.Identity -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($r -and $typeMap.ContainsKey([string]$r.RecipientTypeDetails)) {
        $results.Add([PSCustomObject]@{
            Group              = $r.DisplayName
            PrimarySmtpAddress = [string]$r.PrimarySmtpAddress
            GroupType          = $typeMap[[string]$r.RecipientTypeDetails]
            Permission         = 'SendAs'
        })
    }
}

# --- Send on Behalf (GrantSendOnBehalfTo) ---
function Test-Delegate($list) {
    foreach ($d in $list) { if ($ids -contains $d.ToString()) { return $true } }
    return $false
}

Write-Verbose "Checking Send on Behalf..."
$sources = @(
    @{ Type = 'DL';        Items = { Get-DistributionGroup -ResultSize Unlimited } }
    @{ Type = 'DDL';       Items = { Get-DynamicDistributionGroup -ResultSize Unlimited } }
    @{ Type = 'M365Group'; Items = { Get-UnifiedGroup -ResultSize Unlimited } }
)
foreach ($s in $sources) {
    foreach ($g in (& $s.Items)) {
        if ($g.GrantSendOnBehalfTo -and (Test-Delegate $g.GrantSendOnBehalfTo)) {
            $results.Add([PSCustomObject]@{
                Group              = $g.DisplayName
                PrimarySmtpAddress = [string]$g.PrimarySmtpAddress
                GroupType          = $s.Type
                Permission         = 'SendOnBehalf'
            })
        }
    }
}

if ($results.Count -eq 0) {
    Write-Host "No Send As or Send on Behalf permissions found on groups for $User."
}
$results | Sort-Object GroupType, Group
