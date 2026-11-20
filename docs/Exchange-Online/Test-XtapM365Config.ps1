<#
.SYNOPSIS
  Read-only validation of Microsoft 365 Cross-Tenant Access Policy (XTAP) settings
  for Free/Busy, MailTips and Calendar Sharing.

.DESCRIPTION
  Checks, for the signed-in tenant:
    - Default policy: M365 collaboration inbound and M365 capabilities (flags broad access).
    - Each partner (or only -PartnerTenantId): M365 collaboration inbound trust, expected
      capabilities present/allowed, unexpected allowed capabilities, resource scope.
    - Optional reciprocity check against a snapshot exported from the partner tenant
      (-PeerSnapshotPath), because XTAP capabilities are inbound-only and both sides must allow.
  Nothing is changed. Requires Policy.Read.All (delegated) and a Global/Security Reader or higher role.

.PARAMETER PartnerTenantId
  Partner tenant IDs to validate. Default: every partner configured in the tenant.

.PARAMETER ExpectedCapabilities
  Capability names every validated partner should have allowed.

.PARAMETER ExportPath
  Writes a JSON snapshot of this tenant's settings. Run in the partner tenant too,
  then pass that file to -PeerSnapshotPath for the reciprocity check.

.PARAMETER PeerSnapshotPath
  Snapshot exported from the other tenant.

.PARAMETER AuthMethod
  Interactive (default, delegated browser sign-in), ClientSecret, Certificate
  (app-only; needs Policy.Read.All application permission with admin consent),
  ManagedIdentity (Azure-hosted), AccessToken (pre-acquired token, SecureString),
  ExistingContext (reuse a prior Connect-MgGraph session).

.PARAMETER TenantId / ClientId / ClientSecret / CertificateThumbprint / Certificate / AccessToken / Environment
  Inputs for the chosen auth method. ClientId also selects a user-assigned managed identity
  or a custom app for interactive sign-in. Environment: Global, USGov, USGovDoD, China.

.PARAMETER ClientSecretEnvVar / KeyVaultName / KeyVaultSecretName
  For -AuthMethod ClientSecret when -ClientSecret is not given: read the secret from Azure Key Vault
  (needs Az.KeyVault and Connect-AzAccount) or from an environment variable (default XTAP_CLIENT_SECRET).

.PARAMETER ResultPath
  Writes the results to a file: JSON if the path ends in .json, otherwise CSV.

.PARAMETER PassThru
  Emits the result objects (Scope, Check, Status, Detail) to the pipeline.

.NOTES
  Partner display names are shown when the signed-in identity can call findTenantInformationByTenantId
  (CrossTenantInformation.ReadBasic.All); otherwise only the tenant ID is shown.
  Uses Microsoft Graph beta endpoints, which Microsoft may change without notice.
  Exit code is 1 when any check fails.

.EXAMPLE
  .\Test-XtapM365Config.ps1 -AuthMethod ClientSecret -TenantId <id> -ClientId <appId> -ClientSecret (Read-Host -AsSecureString)

.EXAMPLE
  .\Test-XtapM365Config.ps1 -AuthMethod ClientSecret -TenantId <id> -ClientId <appId> -KeyVaultName <vault> -KeyVaultSecretName <secret> -ResultPath .\xtap.csv

.EXAMPLE
  .\Test-XtapM365Config.ps1 -AuthMethod Certificate -TenantId <id> -ClientId <appId> -CertificateThumbprint <thumb>

.EXAMPLE
  .\Test-XtapM365Config.ps1 -PartnerTenantId 00000000-0000-0000-0000-000000000000 -ExportPath .\tenantA.json

.EXAMPLE
  .\Test-XtapM365Config.ps1 -PartnerTenantId <tenantA-id> -PeerSnapshotPath .\tenantA.json
#>
[CmdletBinding()]
param(
    [string[]]$PartnerTenantId,
    [string[]]$ExpectedCapabilities = @(
        'crossTenantCalendarSharingFreeBusyReviewer',
        'crossTenantMailTipsAll',
        'crossTenantCalendarAvailabilityLimitedDetails'
    ),
    [string]$ExportPath,
    [string]$PeerSnapshotPath,
    [ValidateSet('Interactive', 'ClientSecret', 'Certificate', 'ManagedIdentity', 'AccessToken', 'ExistingContext')]
    [string]$AuthMethod = 'Interactive',
    [string]$TenantId,
    [string]$ClientId,
    [securestring]$ClientSecret,
    [string]$ClientSecretEnvVar = 'XTAP_CLIENT_SECRET',
    [string]$KeyVaultName,
    [string]$KeyVaultSecretName,
    [string]$CertificateThumbprint,
    [System.Security.Cryptography.X509Certificates.X509Certificate2]$Certificate,
    [securestring]$AccessToken,
    [ValidateSet('Global', 'USGov', 'USGovDoD', 'China')]
    [string]$Environment = 'Global',
    [string]$ResultPath,
    [switch]$PassThru
)

$ErrorActionPreference = 'Stop'
# The M365 capabilities (m365Capabilities) endpoints are only available in Graph beta, so this
# script can break if Microsoft changes the beta schema. Re-validate after Graph updates.
$base = 'https://graph.microsoft.com/beta/policies/crossTenantAccessPolicy'
$results = New-Object System.Collections.Generic.List[object]
$partnerNames = @{}

function Add-Result($Scope, $Check, $Status, $Detail) {
    if ($partnerNames.ContainsKey($Scope)) { $Scope = "$Scope ($($partnerNames[$Scope]))" }
    $results.Add([pscustomobject]@{ Scope = $Scope; Check = $Check; Status = $Status; Detail = $Detail })
}

function Get-PartnerName($Id) {
    try {
        $t = Invoke-MgGraphRequest -Method GET -Uri "https://graph.microsoft.com/v1.0/tenantRelationships/findTenantInformationByTenantId(tenantId='$Id')"
        if ($t.displayName) { return [string]$t.displayName }
    } catch { }   # needs CrossTenantInformation.ReadBasic.All; names are optional
    return $null
}

function Get-Graph($Uri) {
    $items = @()
    while ($Uri) {
        $r = Invoke-MgGraphRequest -Method GET -Uri $Uri
        if ($r.ContainsKey('value')) { $items += $r.value } else { return $r }
        $Uri = $r['@odata.nextLink']
    }
    return $items
}

function Get-CapabilitySummary($Caps) {
    foreach ($c in $Caps) {
        $inc = @($c.inboundAccess.resourceScopes.included)
        [pscustomobject]@{
            Name    = $c.name
            Allowed = [bool]$c.inboundAccess.isAllowed
            Scope   = (($inc | ForEach-Object { "$($_.resourceId)/$($_.resourceType)" }) -join ',')
        }
    }
}

# State: Allowed (all users), Scoped (allowed for specific users/groups), Blocked, NotConfigured (inherits default)
function Get-TrustState($Policy) {
    $in = $Policy.m365CollaborationInbound
    $u = $in.users
    if (-not $u -or -not $u.accessType) { return 'NotConfigured' }
    if ($in.applications.accessType -eq 'blocked') { return 'Blocked' }
    if ($u.accessType -ne 'allowed') { return 'Blocked' }
    if (@($u.targets.target) -contains 'AllUsers') { return 'Allowed' }
    return 'Scoped'
}

# Connect
if (-not (Get-Module -ListAvailable Microsoft.Graph.Authentication)) {
    throw 'Install the Microsoft.Graph.Authentication module: Install-Module Microsoft.Graph.Authentication -Scope CurrentUser'
}
Import-Module Microsoft.Graph.Authentication
function Require($Value, $Name) {
    if (-not $Value) { throw "-$Name is required for -AuthMethod $AuthMethod." }
}

if ($AuthMethod -eq 'ExistingContext') {
    if (-not (Get-MgContext)) { throw 'No existing Graph session. Run Connect-MgGraph first or choose another -AuthMethod.' }
} else {
    $connect = @{ NoWelcome = $true; ContextScope = 'Process'; Environment = $Environment }
    switch ($AuthMethod) {
        'Interactive' {
            $connect.Scopes = 'Policy.Read.All'
            if ($TenantId) { $connect.TenantId = $TenantId }
            if ($ClientId) { $connect.ClientId = $ClientId }
        }
        'ClientSecret' {
            Require $TenantId 'TenantId'; Require $ClientId 'ClientId'
            if (-not $ClientSecret -and $KeyVaultName -and $KeyVaultSecretName) {
                if (-not (Get-Command Get-AzKeyVaultSecret -ErrorAction SilentlyContinue)) { throw 'Az.KeyVault is required for -KeyVaultName (Install-Module Az.KeyVault) and an Az sign-in (Connect-AzAccount).' }
                $ClientSecret = (Get-AzKeyVaultSecret -VaultName $KeyVaultName -Name $KeyVaultSecretName).SecretValue
            }
            if (-not $ClientSecret) {
                $envValue = [Environment]::GetEnvironmentVariable($ClientSecretEnvVar)
                if ($envValue) { $ClientSecret = ConvertTo-SecureString $envValue -AsPlainText -Force }
            }
            if (-not $ClientSecret) { throw "-ClientSecret, -KeyVaultName/-KeyVaultSecretName or the $ClientSecretEnvVar environment variable is required for -AuthMethod ClientSecret." }
            $connect.TenantId = $TenantId
            $connect.ClientSecretCredential = New-Object System.Management.Automation.PSCredential($ClientId, $ClientSecret)
        }
        'Certificate' {
            Require $TenantId 'TenantId'; Require $ClientId 'ClientId'
            if (-not ($Certificate -or $CertificateThumbprint)) { throw '-Certificate or -CertificateThumbprint is required for -AuthMethod Certificate.' }
            $connect.TenantId = $TenantId
            $connect.ClientId = $ClientId
            if ($Certificate) { $connect.Certificate = $Certificate } else { $connect.CertificateThumbprint = $CertificateThumbprint }
        }
        'ManagedIdentity' {
            $connect.Identity = $true
            if ($ClientId) { $connect.ClientId = $ClientId }   # user-assigned identity
        }
        'AccessToken' {
            Require $AccessToken 'AccessToken'
            $connect.AccessToken = $AccessToken
        }
    }
    Connect-MgGraph @connect | Out-Null
}

# App-only identities may lack Organization.Read.All, so fall back to -TenantId / context
try {
    $org = @(Get-Graph 'https://graph.microsoft.com/v1.0/organization')[0]
    $tenantId = $org.id
    $orgName = $org.displayName
} catch {
    $tenantId = if ($TenantId) { $TenantId } else { (Get-MgContext).TenantId }
    $orgName = 'unknown (organization not readable)'
    if (-not $tenantId) { throw "Could not determine tenant ID: $($_.Exception.Message)" }
}
Write-Host "Tenant: $orgName ($tenantId)  Auth: $AuthMethod" -ForegroundColor Cyan

# Default policy
$default = Get-Graph "$base/default"
$defaultCaps = @(Get-CapabilitySummary (Get-Graph "$base/default/m365Capabilities"))

$defaultState = Get-TrustState $default
switch ($defaultState) {
    'Allowed' { Add-Result 'Default' 'M365 collaboration inbound' 'WARN' 'Allowed for all users from ALL external tenants.' }
    'Scoped'  { Add-Result 'Default' 'M365 collaboration inbound' 'WARN' 'Allowed for specific users/groups from ALL external tenants.' }
    default   { Add-Result 'Default' 'M365 collaboration inbound' 'PASS' 'Blocked by default; only partners with an explicit allow can use it.' }
}
foreach ($c in $defaultCaps) {
    if ($c.Allowed -and $c.Name -match 'Reviewer') {
        Add-Result 'Default' "Capability $($c.Name)" 'WARN' "Allowed ($($c.Scope)); gives full calendar details."
    } elseif ($c.Allowed -and $c.Name -match '^anonymous') {
        Add-Result 'Default' "Capability $($c.Name)" 'WARN' "Anonymous publishing allowed ($($c.Scope))."
    } else {
        Add-Result 'Default' "Capability $($c.Name)" 'INFO' "Allowed=$($c.Allowed) Scope=$($c.Scope)"
    }
}

# Partners
$partners = @(Get-Graph "$base/partners")
if ($PartnerTenantId) {
    foreach ($id in $PartnerTenantId) {
        if (-not ($partners | Where-Object { $_.tenantId -eq $id })) {
            Add-Result $id 'Partner configured' 'FAIL' 'No partner entry found in this tenant.'
        }
    }
    $partners = @($partners | Where-Object { $PartnerTenantId -contains $_.tenantId })
}
if (-not $partners) { Add-Result 'Partners' 'Partners found' 'WARN' 'No partner configurations to validate.' }

$snapshotPartners = @()
foreach ($p in $partners) {
    $id = $p.tenantId
    $name = Get-PartnerName $id
    if ($name) { $partnerNames[$id] = $name }
    try {
        $partnerCaps = @(Get-CapabilitySummary (Get-Graph "$base/partners/$id/m365Capabilities"))

        # Effective trust: a partner without its own setting inherits the default policy
        $state = Get-TrustState $p
        $inherited = $state -eq 'NotConfigured'
        $effective = if ($inherited) { $defaultState } else { $state }
        $src = if ($inherited) { ' (inherited from default)' } else { '' }
        $trustOk = $effective -in 'Allowed', 'Scoped'

        # Effective capabilities: partner entry wins, otherwise the default entry applies
        $caps = @($partnerCaps)
        foreach ($d in $defaultCaps) {
            if (-not ($partnerCaps | Where-Object { $_.Name -eq $d.Name })) {
                $caps += [pscustomobject]@{ Name = $d.Name; Allowed = $d.Allowed; Scope = $d.Scope; Inherited = $true }
            }
        }
        $snapshotPartners += [pscustomobject]@{
            tenantId = $id; m365InboundAllowed = $trustOk; m365InboundState = $effective
            m365InboundInherited = $inherited; capabilities = $caps
        }

        switch ($effective) {
            'Allowed' { Add-Result $id 'M365 collaboration inbound (trust)' 'PASS' "Allowed for all users$src." }
            'Scoped'  { Add-Result $id 'M365 collaboration inbound (trust)' 'PASS' "Allowed for specific users/groups$src." }
            default   { Add-Result $id 'M365 collaboration inbound (trust)' 'FAIL' "Blocked$src; capabilities will not take effect." }
        }

        foreach ($name in $ExpectedCapabilities) {
            $c = $caps | Where-Object { $_.Name -eq $name }
            $csrc = if ($c.Inherited) { ' (inherited from default)' } else { '' }
            if (-not $c)             { Add-Result $id "Expected $name" 'FAIL' 'Missing.' }
            elseif (-not $c.Allowed) { Add-Result $id "Expected $name" 'FAIL' "Disabled$csrc." }
            elseif ($c.Scope -eq 'All/user' -or $c.Scope -eq 'All/group') {
                Add-Result $id "Expected $name" 'PASS' "Allowed for all users$csrc (consider limiting to a security group)."
            } else { Add-Result $id "Expected $name" 'PASS' "Allowed$csrc. Scope=$($c.Scope)" }
        }
        foreach ($c in ($partnerCaps | Where-Object { $_.Allowed -and $ExpectedCapabilities -notcontains $_.Name })) {
            Add-Result $id "Extra $($c.Name)" 'WARN' "Allowed but not in the expected list. Scope=$($c.Scope)"
        }
        if ($p.isInMultiTenantOrganization) { Add-Result $id 'Multitenant organization' 'INFO' 'Partner is in a multitenant organization.' }
    } catch {
        Add-Result $id 'Partner evaluation' 'FAIL' "Could not read partner settings: $($_.Exception.Message)"
    }
}

# Reciprocity
if ($PeerSnapshotPath) {
    $peer = Get-Content $PeerSnapshotPath -Raw | ConvertFrom-Json
    $peerId = $peer.tenantId
    $mine = $snapshotPartners | Where-Object { $_.tenantId -eq $peerId }
    $theirs = $peer.partners | Where-Object { $_.tenantId -eq $tenantId }
    $scope = "Reciprocity with $peerId"
    if (-not $mine)   { Add-Result $scope 'This tenant has peer as partner' 'FAIL' 'Peer not among validated partners here.' }
    if (-not $theirs) { Add-Result $scope 'Peer has this tenant as partner' 'FAIL' 'This tenant is not a partner in the peer snapshot.' }
    if ($mine -and $theirs) {
        if ($theirs.m365InboundAllowed) { Add-Result $scope 'Peer trust' 'PASS' 'Peer allows M365 collaboration inbound from this tenant.' }
        else { Add-Result $scope 'Peer trust' 'FAIL' 'Peer does not allow M365 collaboration inbound from this tenant.' }
        foreach ($name in $ExpectedCapabilities) {
            $a = $mine.capabilities | Where-Object { $_.Name -eq $name -and $_.Allowed }
            $b = $theirs.capabilities | Where-Object { $_.Name -eq $name -and $_.Allowed }
            if ($a -and $b) { Add-Result $scope $name 'PASS' 'Allowed on both sides.' }
            else { Add-Result $scope $name 'FAIL' ("Allowed here: {0}; allowed at peer: {1}" -f [bool]$a, [bool]$b) }
        }
    }
}

# Output
$order = @{ FAIL = 0; WARN = 1; PASS = 2; INFO = 3 }
$sorted = @($results | Sort-Object { $order[$_.Status] }, Scope)
$sorted | Format-Table -AutoSize -Wrap | Out-Host
$counts = $results | Group-Object Status | ForEach-Object { "$($_.Name)=$($_.Count)" }
Write-Host ("Summary: " + ($counts -join '  ')) -ForegroundColor Cyan

if ($ExportPath) {
    [pscustomobject]@{
        tenantId = $tenantId
        exported = (Get-Date).ToString('s')
        partners = $snapshotPartners
        default  = @{ capabilities = $defaultCaps }
    } | ConvertTo-Json -Depth 8 | Set-Content -Path $ExportPath -Encoding UTF8
    Write-Host "Snapshot written to $ExportPath" -ForegroundColor Cyan
}

if ($ResultPath) {
    if ($ResultPath -match '\.json$') { $sorted | ConvertTo-Json -Depth 4 | Set-Content -Path $ResultPath -Encoding UTF8 }
    else { $sorted | Export-Csv -Path $ResultPath -NoTypeInformation -Encoding UTF8 }
    Write-Host "Results written to $ResultPath" -ForegroundColor Cyan
}
if ($PassThru) { $sorted }

if ($results | Where-Object Status -eq 'FAIL') { exit 1 }
