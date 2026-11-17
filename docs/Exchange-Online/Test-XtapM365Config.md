# Test-XtapM365Config

Read-only validation of the Microsoft 365 **Cross-Tenant Access Policy (XTAP)** settings behind **Free/Busy**, **MailTips** and **Calendar Sharing** between tenants. Nothing is changed.

[Download Test-XtapM365Config.ps1](Test-XtapM365Config.ps1)

## What it checks

- **Default policy:** flags M365 collaboration inbound allowed from all external tenants, and broad capabilities such as calendar reviewer or anonymous publishing.
- **Each partner** (or only the ones in `-PartnerTenantId`): inbound trust is allowed, expected capabilities are present and enabled, unexpected allowed capabilities, and resource scope. Settings a partner doesn't define are evaluated against the default policy and labelled `(inherited from default)`. Trust limited to specific users or groups is reported as scoped, not blocked.
- **Errors:** if one partner can't be read, it is reported as a FAIL and the remaining partners are still checked.
- **Reciprocity (optional):** compares against a snapshot exported from the partner tenant, because XTAP capabilities are inbound-only and **both sides must allow**.

## Requirements

- The [Microsoft.Graph.Authentication](https://learn.microsoft.com/powershell/microsoftgraph/installation) module.
- Delegated sign-in: `Policy.Read.All` and a Security Reader, Global Reader or higher role.
- App-only sign-in: the `Policy.Read.All` **application** permission with admin consent.

## Authentication methods

| `-AuthMethod` | Required parameters | Notes |
|---|---|---|
| `Interactive` (default) | none | Browser sign-in. Optional `-TenantId`, `-ClientId`. |
| `ClientSecret` | `-TenantId`, `-ClientId`, `-ClientSecret` | App-only. Secret is a `SecureString`. |
| `Certificate` | `-TenantId`, `-ClientId`, `-CertificateThumbprint` or `-Certificate` | App-only, no secret to store. |
| `ManagedIdentity` | none | For Azure-hosted runs. Add `-ClientId` for a user-assigned identity. |
| `AccessToken` | `-AccessToken` | Pre-acquired Graph token as a `SecureString`. |
| `ExistingContext` | none | Reuses a prior `Connect-MgGraph` session. |

`-Environment` selects the cloud: `Global` (default), `USGov`, `USGovDoD` or `China`.

!!! note
    App-only identities may not be able to read `/organization`. The script then falls back to `-TenantId` or the session's tenant ID.

## Usage

```powershell
# Interactive, all partners
.\Test-XtapM365Config.ps1

# One partner, export this tenant's snapshot
.\Test-XtapM365Config.ps1 -PartnerTenantId <partner-tenant-id> -ExportPath .\tenantA.json

# Reciprocity check from the other tenant
.\Test-XtapM365Config.ps1 -PartnerTenantId <tenantA-id> -PeerSnapshotPath .\tenantA.json

# App-only with a client secret
.\Test-XtapM365Config.ps1 -AuthMethod ClientSecret -TenantId <tenant-id> -ClientId <app-id> `
    -ClientSecret (Read-Host -AsSecureString)

# App-only with a certificate
.\Test-XtapM365Config.ps1 -AuthMethod Certificate -TenantId <tenant-id> -ClientId <app-id> `
    -CertificateThumbprint <thumbprint>
```

## Parameters

| Parameter | Description |
|---|---|
| `-PartnerTenantId` | Partner tenant IDs to validate. Default: every configured partner. |
| `-ExpectedCapabilities` | Capabilities each partner should allow. Default: `crossTenantCalendarSharingFreeBusyReviewer`, `crossTenantMailTipsAll`, `crossTenantCalendarAvailabilityLimitedDetails`. |
| `-ExportPath` | Writes a JSON snapshot of this tenant's settings. |
| `-PeerSnapshotPath` | Snapshot exported from the other tenant, for the reciprocity check. |
| `-AuthMethod`, `-TenantId`, `-ClientId`, `-ClientSecret`, `-CertificateThumbprint`, `-Certificate`, `-AccessToken`, `-Environment` | Sign-in options, see above. |

## Output

A table sorted FAIL, WARN, PASS, INFO with `Scope`, `Check`, `Status` and `Detail`, then a summary line. The script exits with code `1` if any check fails, so it can run in a pipeline.

!!! tip
    Run it in a lab tenant first. The script only reads policy, but the partner settings it reports are what control calendar visibility.
