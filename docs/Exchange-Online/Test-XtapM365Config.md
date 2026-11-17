# Validate your Microsoft 365 cross-tenant access policy when migrating Free/Busy, MailTips and calendar sharing

Microsoft is moving cross-tenant Free/Busy, MailTips and calendar sharing from **Organization Relationships** and **Sharing Policies** to the **Microsoft 365 cross-tenant access policy (XTAP)**. The old model depends on Exchange Web Services (EWS) and high-privilege access, both of which are being retired. Microsoft's guide, [Migrate to Microsoft 365 Cross-Tenant Access Policy for sharing Free/Busy, Calendars, and MailTips](https://learn.microsoft.com/exchange/sharing/migrate-to-m365-xtap), walks through the migration in four parts.

This article adds a read-only validation script for the part Microsoft's guide leaves to you: confirming the XTAP settings are what you intended, in both tenants, before you disable and remove the old configuration.

[Download Test-XtapM365Config.ps1](Test-XtapM365Config.ps1)

!!! note
    XTAP for Free/Busy, MailTips and calendar sharing is rolling out and may not have reached your tenant yet. Check the Message Center and the Exchange Team Blog before you plan the migration.

## The migration in four parts

| Part | What you do | Where this script helps |
|---|---|---|
| 1. Inventory | Review `Get-OrganizationRelationship`, `Get-AvailabilityAddressSpace` and `Get-SharingPolicy`, and decide what to migrate. | Not covered. The script only reads XTAP, not the Exchange configuration. |
| 2. Configure XTAP | Enable the **Microsoft 365 collaboration** trust per partner, then add the matching capabilities. | Check that trust and every capability landed as intended. |
| 3. Test | Disable the old configuration in both tenants and validate sharing with the partner's admin. | Check both tenants agree before you disable anything. |
| 4. Clean up | Remove the old Organization Relationships, Availability Address Spaces and Sharing Policies. | Re-run to confirm nothing is missing before you remove them. |

## Things to know before you validate

- **XTAP is inbound-only.** Each tenant controls what the *other* tenant can read. For two-way sharing, both tenants need complementary policies. The script's reciprocity check is built for this.
- **The trust comes first.** Capabilities have no effect until the partner has M365 collaboration inbound allowed.
- **Precedence differs.** Existing Organization Relationships and Availability Address Spaces win over XTAP, so disable them to test Free/Busy and MailTips. For calendar sharing, XTAP wins over Sharing Policies, so you can test while they remain enabled.
- **Anonymous publishing is default-policy only.** `anonymousCalendarSharing…` capabilities can't be set per partner, and an existing Anonymous entry in a Sharing Policy can still apply.
- **Hybrid and on-premises partners aren't covered.** Keep their Sharing Policies enabled.
- **Capability names are case-sensitive.**

## Capabilities the script validates

By default the script expects each partner to allow three of these (see below). Override them with `-ExpectedCapabilities` to match your own mapping.

| Capability | What it grants | Replaces |
|---|---|---|
| `crossTenantCalendarAvailabilityBasic` | Free/Busy, time only | Organization Relationship `AvailabilityOnly`, or an Availability Address Space |
| `crossTenantCalendarAvailabilityLimitedDetails` | Free/Busy with subject and location | Organization Relationship `LimitedDetails` |
| `crossTenantMailTipsLimited` | MailTips limited to those that prevent an NDR or auto reply | Organization Relationship `MailTipsAccessLevel Limited` |
| `crossTenantMailTipsAll` | All MailTips, including out-of-office and recipient info | Organization Relationship `MailTipsAccessLevel All` |
| `crossTenantCalendarSharingFreeBusySimple` | Calendar sharing, time only | Sharing Policy `CalendarSharingFreeBusySimple` |
| `crossTenantCalendarSharingFreeBusyDetail` | Calendar sharing with subject and location | Sharing Policy `CalendarSharingFreeBusyDetail` |
| `crossTenantCalendarSharingFreeBusyReviewer` | Calendar sharing, full details | Sharing Policy `CalendarSharingFreeBusyReviewer` |

The built-in default list is `crossTenantCalendarSharingFreeBusyReviewer`, `crossTenantMailTipsAll` and `crossTenantCalendarAvailabilityLimitedDetails`. Pass your own list to match the level you migrated. For example, for time-only Free/Busy and limited MailTips:

```powershell
.\Test-XtapM365Config.ps1 -PartnerTenantId <partner-tenant-id> `
    -ExpectedCapabilities crossTenantCalendarAvailabilityBasic, crossTenantMailTipsLimited
```

## What the script checks

- **Default policy:** flags M365 collaboration inbound allowed from all external tenants, and broad capabilities such as calendar reviewer or anonymous publishing. This is where wildcard (`*`) and Anonymous Sharing Policy entries end up.
- **Each partner** (or only those in `-PartnerTenantId`): inbound trust is allowed, expected capabilities are present and enabled, unexpected allowed capabilities, and resource scope. Settings a partner doesn't define are evaluated against the default policy and labelled `(inherited from default)`. Trust limited to specific users or groups is reported as scoped, not blocked. The partner tenant name is shown when your identity can look it up.
- **Reciprocity (optional):** compares your tenant with a snapshot exported from the partner tenant, because both sides must allow.
- **Errors:** if one partner can't be read, it is reported as a FAIL and the rest are still checked.

## Requirements

- The [Microsoft.Graph.Authentication](https://learn.microsoft.com/powershell/microsoftgraph/installation) module.
- Delegated sign-in: `Policy.Read.All` and a Security Reader, Global Reader or higher role.
- App-only sign-in: the `Policy.Read.All` **application** permission with admin consent.
- Optional, for partner names: `CrossTenantInformation.ReadBasic.All`.

The script never writes. Creating the trust and the capabilities needs the write scopes from Microsoft's guide (`Policy.ReadWrite.CrossTenantAccess`, `Policy.ReadWrite.CrossTenantCapability`) and is done with the steps in Part 2 of that guide.

## Validate during the migration

**After Part 2, in your tenant.** Check the partner you configured, and export a snapshot:

```powershell
.\Test-XtapM365Config.ps1 -PartnerTenantId <partner-tenant-id> -ExportPath .\tenantA.json
```

**In the partner tenant.** The partner's admin runs the same script, pointing at your tenant, and passes your snapshot to get the reciprocity check:

```powershell
.\Test-XtapM365Config.ps1 -PartnerTenantId <your-tenant-id> -PeerSnapshotPath .\tenantA.json
```

Every `FAIL` in the reciprocity section means one side hasn't allowed that capability, so sharing in that direction won't work. Fix these *before* you disable the Organization Relationship or Sharing Policy in Part 3.

**Before Part 4.** Run it once more against all partners and keep the results as a record:

```powershell
.\Test-XtapM365Config.ps1 -ResultPath .\xtap-before-cleanup.csv
```

## Reading the results

| Status | Meaning in a migration |
|---|---|
| `FAIL` | Trust or an expected capability is missing or disabled, or reciprocity is broken. Sharing won't work yet. Don't clean up the old configuration. |
| `WARN` | Works, but broader than you may want: for example the default policy allows anonymous publishing, or a partner has capabilities you didn't list. |
| `PASS` | As expected. A PASS for `all users` is a reminder to consider limiting scope to a security group, as Microsoft's guide describes. |
| `INFO` | Context, such as the other default capabilities or multitenant organization membership. |

!!! tip
    If your existing Sharing Policies were assigned to different mailboxes, Microsoft's guide says to use security groups to build comparable policies. The script shows the scope (`<groupId>/group` or `All/user`) for each capability, so you can confirm the group was applied.

The script exits with code `1` if any check fails, so you can run it in a pipeline.

## Sign-in options

| `-AuthMethod` | Required parameters | Notes |
|---|---|---|
| `Interactive` (default) | none | Browser sign-in. Optional `-TenantId`, `-ClientId`. |
| `ClientSecret` | `-TenantId`, `-ClientId`, plus a secret from `-ClientSecret` (`SecureString`), Azure Key Vault (`-KeyVaultName`, `-KeyVaultSecretName`) or the `XTAP_CLIENT_SECRET` environment variable (name set with `-ClientSecretEnvVar`) | App-only. Key Vault needs the Az.KeyVault module and `Connect-AzAccount`. |
| `Certificate` | `-TenantId`, `-ClientId`, `-CertificateThumbprint` or `-Certificate` | App-only, no secret to store. |
| `ManagedIdentity` | none | For Azure-hosted runs. Add `-ClientId` for a user-assigned identity. |
| `AccessToken` | `-AccessToken` | Pre-acquired Graph token as a `SecureString`. |
| `ExistingContext` | none | Reuses a prior `Connect-MgGraph` session. |

`-Environment` selects the cloud: `Global` (default), `USGov`, `USGovDoD` or `China`. App-only identities may not be able to read `/organization`. The script then falls back to `-TenantId` or the session's tenant ID.

## Parameters

| Parameter | Description |
|---|---|
| `-PartnerTenantId` | Partner tenant IDs to validate. Default: every configured partner. |
| `-ExpectedCapabilities` | Capabilities each partner should allow. See the table above for the default. |
| `-ExportPath` | Writes a JSON snapshot of this tenant's settings. |
| `-PeerSnapshotPath` | Snapshot exported from the other tenant, for the reciprocity check. |
| `-ResultPath` | Writes the results to a file: JSON if the path ends in `.json`, otherwise CSV. |
| `-PassThru` | Returns the result objects (`Scope`, `Check`, `Status`, `Detail`) to the pipeline. |
| `-AuthMethod`, `-TenantId`, `-ClientId`, `-ClientSecret`, `-ClientSecretEnvVar`, `-KeyVaultName`, `-KeyVaultSecretName`, `-CertificateThumbprint`, `-Certificate`, `-AccessToken`, `-Environment` | Sign-in options, see above. |

!!! note
    The script uses Microsoft Graph **beta** endpoints for the M365 capabilities, which Microsoft can change without notice. Re-validate after Graph updates.

## References

- [Migrate to Microsoft 365 Cross-Tenant Access Policy for sharing Free/Busy, Calendars, and MailTips](https://learn.microsoft.com/exchange/sharing/migrate-to-m365-xtap)
- [Microsoft 365 cross-tenant access policy Microsoft Graph API overview](https://learn.microsoft.com/graph/api/resources/m365-cross-tenant-access-policy-overview)
- [Deprecation of EWS in Exchange Online](https://learn.microsoft.com/exchange/clients-and-mobile-in-exchange-online/deprecation-of-ews-exchange-online)
