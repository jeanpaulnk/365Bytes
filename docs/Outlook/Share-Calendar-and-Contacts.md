# Share Calendars and Contacts in Microsoft 365

How to share calendars and contacts in Exchange Online, either through **a shared mailbox for a team** or by **one person sharing their own folders**, with PowerShell equivalents and the external sharing policy.

## Pick the right approach

| You want... | Use | Who sets it up |
|---|---|---|
| A team calendar / contact list everyone can edit | **Shared mailbox** + Full Access | Admin |
| To let a colleague see or edit *your* calendar | **Calendar sharing** (folder permission) | User |
| To share *your* contacts folder | **Contacts sharing** (classic Outlook only) | User |
| To share with people in another company | Calendar/contacts sharing + **cross-tenant access policy** (calendars) or **sharing policy** (contacts, on-premises) | User + Admin |

!!! note
    A shared mailbox also receives email. Anyone given access to its calendar can also read and reply to its mail.

## Option A: Team calendar and contacts with a shared mailbox

### 1. Create the shared mailbox

**Microsoft 365 admin center:** **Teams & groups > Shared mailboxes > Add a shared mailbox**, enter a name and address, then add members.

**PowerShell:**

```powershell
Connect-ExchangeOnline

New-Mailbox -Shared -Name "Team Calendar" -PrimarySmtpAddress teamcal@domain.com
```

### 2. Grant access

For a few people, add them directly. For a large or changing group, grant a **mail-enabled security group** so you only manage membership in one place.

```powershell
# Individual user (AutoMapping adds it to their classic Outlook automatically)
Add-MailboxPermission -Identity teamcal@domain.com -User alice@domain.com -AccessRights FullAccess -AutoMapping $true

# Security group (members get access; AutoMapping does not apply to groups)
Add-MailboxPermission -Identity teamcal@domain.com -User "SG-TeamCalendar" -AccessRights FullAccess
```

!!! tip
    Only need the calendar, not the mailbox? Skip Full Access and grant folder rights instead:
    `Add-MailboxFolderPermission -Identity teamcal@domain.com:\Calendar -User SG-TeamCalendar -AccessRights Editor`

### 3. Open it

| Client | Calendar | Contacts |
|---|---|---|
| Classic Outlook | Appears under **My Calendars** automatically (AutoMapping) | Appears under **My Contacts** |
| New Outlook | **Calendar > Add calendar > Add from directory** | Not supported |
| Outlook on the web | **Calendar > Add calendar > Add from directory** | Not supported |

For mail in new Outlook / OWA: right-click your account in the folder pane > **Add shared folder or mailbox**. It can take up to an hour after access is granted before it shows.

## Option B: Share your own calendar

**Outlook (classic, new or web):** open **Calendar**, select **Share** (or right-click the calendar > **Sharing and permissions**), add the person and choose a level, then **Send / Share**. The recipient clicks **Accept** / **Add calendar** in the invitation.

| Permission | What they see / do |
|---|---|
| Can view when I'm busy | Free/busy only |
| Can view titles and locations | Time, subject, location |
| Can view all details | Everything except private items |
| Can edit | Create, change and delete items |
| Delegate | Edit + receives meeting requests on your behalf |

**Change or remove access** in the same **Sharing and permissions** pane (or **Calendar Permissions** in classic Outlook).

**Admin equivalent:**

```powershell
# Grant / change
Add-MailboxFolderPermission -Identity user@domain.com:\Calendar -User colleague@domain.com -AccessRights Reviewer
Set-MailboxFolderPermission -Identity user@domain.com:\Calendar -User colleague@domain.com -AccessRights Editor

# Review / remove
Get-MailboxFolderPermission -Identity user@domain.com:\Calendar
Remove-MailboxFolderPermission -Identity user@domain.com:\Calendar -User colleague@domain.com
```

!!! warning
    Folder names are localised. If `:\Calendar` fails, check `Get-MailboxFolderStatistics user@domain.com -FolderScope Calendar`.

## Option C: Share your contacts folder

Only **classic Outlook for Windows** can send a contacts sharing invitation.

1. Go to **People**, select the contacts folder.
2. **Home > Share Contacts**, enter the recipient, and **Send**.
3. To change or remove access: right-click the folder > **Properties > Permissions**.

PowerShell works for any client: `Add-MailboxFolderPermission -Identity user@domain.com:\Contacts -User colleague@domain.com -AccessRights Reviewer`

## Sharing with people outside your organization

External calendar sharing between Microsoft 365 organizations is moving from the **sharing policy** to the **Microsoft 365 cross-tenant access policy**. The old method relies on Exchange Web Services (EWS), which is being deprecated in Exchange Online. If users get an error like *"This calendar can't be shared with ..."* or *"Folder sharing is not available"*, check both policies.

!!! important
    The cross-tenant access policy is rolling out and may not have reached your tenant yet. Check the Message Center and the [Exchange Team Blog announcement](https://techcommunity.microsoft.com/blog/exchange/cross-tenant-freebusy-mailtips-and-calendar-sharing-are-moving-to-cross-tenant-a/4545169). Plan to migrate after it reaches your tenant and before EWS is deprecated.

### Which policy applies

| Sharing with | Use |
|---|---|
| Another Microsoft 365 organization | **Cross-tenant access policy** (calendar sharing capabilities) |
| On-premises or hybrid Exchange organization | **Sharing policy**. The new policy doesn't cover these, so keep it enabled |
| Anonymous (published calendar URL) | Sharing policy now; an `Anonymous...` capability in the default cross-tenant policy is recommended |
| Contacts folder | Sharing policy (`ContactsSharing`). The migration guide doesn't cover contacts |

For calendars, **the cross-tenant access policy takes precedence**. If a capability applies to the external organization, it's used and the sharing policy is ignored. If none applies, the sharing policy is used. This lets you test while your sharing policies stay enabled.

!!! note
    The policy is **inbound**: each organization controls what external users can see of *its own* calendars. For two-way sharing, **both** organizations must create matching policies.

### Review your current sharing policy

```powershell
Connect-ExchangeOnline

Get-SharingPolicy | Format-List Name, Enabled, Domains, Default

# Which policies are assigned to mailboxes
Get-EXOMailbox -ResultSize Unlimited -RecipientTypeDetails UserMailbox,SharedMailbox -Properties SharingPolicy | Group-Object SharingPolicy | Select-Object Name, Count
```

| Sharing policy value | External recipients can see | Cross-tenant capability that replaces it |
|---|---|---|
| `CalendarSharingFreeBusySimple` | Free/busy only | `CrossTenantCalendarSharingFreeBusySimple` |
| `CalendarSharingFreeBusyDetail` | Free/busy, subject and location | `CrossTenantCalendarSharingFreeBusyDetail` |
| `CalendarSharingFreeBusyReviewer` | All details | `CrossTenantCalendarSharingFreeBusyReviewer` |
| `Anonymous:` entry | Published calendar | `AnonymousCalendarSharingFreeBusy{Simple,Detail,Reviewer}` |

Capability names are **case-sensitive**.

### Set up the cross-tenant access policy

You need **Global Administrator** for the trust step, the partner's **Entra tenant ID**, and the [Microsoft Graph PowerShell SDK](https://learn.microsoft.com/powershell/microsoftgraph/installation). After the trust is in place, Global Administrator or Exchange Administrator can create the capabilities.

**1. Enable Microsoft 365 Collaboration trust** (once per partner tenant):

```powershell
Connect-MgGraph -Scopes "Policy.Read.All,Policy.ReadWrite.CrossTenantAccess,Policy.ReadWrite.CrossTenantCapability" -ContextScope Process

$partnerId = "<partnerTenantId>"
$body = @{
  tenantId = $partnerId
  m365CollaborationInbound = @{
    users = @{
      accessType = "allowed"
      targets = @(@{ target = "AllUsers"; targetType = "user" })
    }
  }
}
New-MgPolicyCrossTenantAccessPolicyPartner -BodyParameter $body
```

**2. Create the calendar sharing capability.** Use a security group to limit whose calendars external users can see, or `All` for everyone. If you have different sharing policies assigned to different mailboxes, use groups to reproduce them.

```powershell
$capability = "CrossTenantCalendarSharingFreeBusyReviewer"   # case-sensitive

# Limit to a group...
$group = @{ resourceId = "<groupId>"; resourceType = "group" }
# ...or everyone
# $group = @{ resourceId = "All"; resourceType = "group" }

$body = @{
  "@odata.type" = "#microsoft.graph.$capability"
  inboundAccess = @{
    isAllowed = $true
    resourceScopes = @{ included = @($group); excluded = @(@{ }) }
  }
}

# Specific partner (replaces a "partner.com:..." entry)
New-MgPolicyCrossTenantAccessPolicyPartnerM365Capability -CrossTenantAccessPolicyConfigurationPartnerTenantId $partnerId -BodyParameter $body

# All external organizations (replaces a "*:..." entry)
New-MgPolicyCrossTenantAccessPolicyDefaultM365Capability -BodyParameter $body
```

**3. Anonymous publishing (if used).** Use an `AnonymousCalendarSharingFreeBusy...` capability with the same body and the **default** command. Anonymous capabilities can't be set per partner. Create it *before* disabling the sharing policy, or published calendars stop working. An `Anonymous` entry with a higher access level than your new capability can still apply, so create it before you test.

### Test and clean up

1. Test with the partner administrator while the sharing policy is still enabled.
2. Once it works, disable the migrated sharing policy to confirm it no longer depends on it. **Skip this for any policy still needed for on-premises, hybrid or anonymous sharing.**

```powershell
Set-SharingPolicy -Identity "<PolicyName>" -Enabled $False   # re-enable with -Enabled $True if needed
```

3. When you're satisfied, remove it: `Remove-SharingPolicy -Identity "<PolicyName>"`.

### Contacts and non-Microsoft 365 partners

Contacts sharing and sharing with on-premises organizations still use the sharing policy:

```powershell
# Contacts for all external domains
Set-SharingPolicy -Identity "Default Sharing Policy" -Domains "*:ContactsSharing"

# Calendar details for an on-premises partner, free/busy for everyone else
Set-SharingPolicy -Identity "Default Sharing Policy" -Domains "partner.com:CalendarSharingFreeBusyReviewer", "*:CalendarSharingFreeBusySimple"
```

**Exchange admin center:** **Organization > Sharing > Individual sharing**, edit the **Default Sharing Policy**.

## Troubleshooting

| Symptom | Check |
|---|---|
| Shared mailbox doesn't appear in classic Outlook | Wait up to an hour; AutoMapping only works for direct user grants, not groups. Add it manually via **Account Settings > More Settings > Advanced**. |
| "You don't have permission" on a shared calendar | `Get-MailboxFolderPermission mailbox:\Calendar` and confirm the user or group is listed. |
| External invite fails | Sharing policy for that domain is missing or too restrictive (see above). |
| Contacts option missing | Contacts sharing needs classic Outlook for Windows. |

## References

- [Share calendar and contacts in Microsoft 365 - Microsoft Learn](https://learn.microsoft.com/microsoft-365-apps/outlook/calendaring/share-calendar-and-contacts)
- [Add-MailboxFolderPermission](https://learn.microsoft.com/powershell/module/exchange/add-mailboxfolderpermission)
- [Set-SharingPolicy](https://learn.microsoft.com/powershell/module/exchange/set-sharingpolicy)
