# Get-GroupSendPermissions

Lists every Distribution List (DL), Dynamic Distribution List (DDL) and Microsoft 365 group on which a given user holds **Send As** or **Send on Behalf** permission in Exchange Online.

[Download Get-GroupSendPermissions.ps1](Get-GroupSendPermissions.ps1)

## Requirements

- The [ExchangeOnlineManagement](https://learn.microsoft.com/powershell/exchange/exchange-online-powershell-v2) module.
- An account with rights to read recipients and recipient permissions (for example **View-Only Organization Management** or **Recipient Management**).

## Where the permissions live

| Permission | Group type | Where it is stored | How to read it |
|---|---|---|---|
| Send As | DL, DDL, M365 group | Recipient ACL | `Get-RecipientPermission -Trustee <user>` |
| Send on Behalf | DL, DDL | `GrantSendOnBehalfTo` | `Get-DistributionGroup` / `Get-DynamicDistributionGroup` |
| Send on Behalf | M365 group | `GrantSendOnBehalfTo` | `Get-UnifiedGroup` |

!!! warning
    Send on Behalf for groups is **not** in a mailbox's `DelegateList`. Checking mailboxes only finds mailbox delegates, not group permissions.

## Usage

```powershell
Connect-ExchangeOnline

.\Get-GroupSendPermissions.ps1 -User user@domain.com

# Export to CSV
.\Get-GroupSendPermissions.ps1 -User user@domain.com |
    Export-Csv .\GroupSendPermissions.csv -NoTypeInformation
```

## Parameters

| Parameter | Description |
|---|---|
| `-User` | UPN, primary SMTP address or alias of the user (trustee) to check. Required. |

## Output

| Column | Description |
|---|---|
| `Group` | Display name of the group. |
| `PrimarySmtpAddress` | Group's primary address. |
| `GroupType` | `DL`, `DDL` or `M365Group`. |
| `Permission` | `SendAs` or `SendOnBehalf`. |

## Script

[Download Get-GroupSendPermissions.ps1](Get-GroupSendPermissions.ps1)

## Quick one-liners

If you only need a fast check, these cmdlets give the same answer per group type:

```powershell
# Send As
Get-RecipientPermission -Trustee user@domain.com -AccessRights SendAs -ResultSize Unlimited

# Send on Behalf
Get-DistributionGroup -ResultSize Unlimited        | Where-Object { $_.GrantSendOnBehalfTo -match "User Name" }
Get-DynamicDistributionGroup -ResultSize Unlimited | Where-Object { $_.GrantSendOnBehalfTo -match "User Name" }
Get-UnifiedGroup -ResultSize Unlimited             | Where-Object { $_.GrantSendOnBehalfTo -match "User Name" }
```

!!! tip
    Test in a lab tenant first. Large tenants can take several minutes because every group is read once.
