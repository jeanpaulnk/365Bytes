# Mark Outlook Email as Read with PowerShell

Mark every unread message in a folder as read: on the user's PC with **classic Outlook**, or server-side with **Microsoft Graph PowerShell**.

## Which method to use

| | Option 1: Outlook (COM) | Option 2: Microsoft Graph |
|---|---|---|
| Runs where | User's Windows PC with classic Outlook | Any machine with PowerShell 7 or 5.1 |
| Works with new Outlook | No (no COM support) | Yes, it changes the mailbox itself |
| Needs admin consent | No | Yes, `Mail.ReadWrite` |
| Good for | One user, one-off cleanup | Admins, other mailboxes, automation |

## Option 1: Classic Outlook (COM)

Run in **Windows PowerShell** on the PC where the Outlook profile is configured. Outlook may be open or closed.

[Download Set-OutlookFolderRead.ps1](Set-OutlookFolderRead.ps1)

!!! note "\"File is not digitally signed\" error"
    Windows marks downloaded files as blocked, and the default execution policy refuses unsigned scripts. Review the script, then unblock it once before running:

    ```powershell
    Unblock-File .\Set-OutlookFolderRead.ps1
    ```

    If it still fails, allow local scripts for the current session only: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`.

Examples:

```powershell
.\Set-OutlookFolderRead.ps1 -Mailbox user@domain.com -Folder "Deleted Items"
.\Set-OutlookFolderRead.ps1 -Mailbox user@domain.com -Folder "Inbox\Projects" -Recurse -WhatIf
```

!!! tip
    `-WhatIf` shows how many items would change without touching anything. The original version also loaded `Microsoft.Office.Interop.Outlook`; that line isn't needed with `New-Object -ComObject`.

## Option 2: Microsoft Graph PowerShell (server-side)

Works for any mailbox you have rights to, and for users on new Outlook, OWA or mobile.

```powershell
Install-Module Microsoft.Graph.Mail -Scope CurrentUser   # once
Connect-MgGraph -Scopes "Mail.ReadWrite"                 # add Mail.ReadWrite.Shared for shared mailboxes

$user   = "user@domain.com"
$folder = "deleteditems"    # well-known name (inbox, deleteditems, junkemail, ...) or a folder ID

$unread = Get-MgUserMailFolderMessage -UserId $user -MailFolderId $folder `
            -Filter "isRead eq false" -Property Id -All

foreach ($m in $unread) {
    Update-MgUserMessage -UserId $user -MessageId $m.Id -BodyParameter @{ isRead = $true }
}
"{0} message(s) marked as read" -f $unread.Count
```

!!! note
    To run this unattended for many mailboxes, use an app registration with the **Mail.ReadWrite** application permission and limit it with an [application access policy / RBAC for Applications](https://learn.microsoft.com/exchange/permissions-exo/application-rbac) so it can't touch every mailbox.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `Retrieving the COM class factory ... failed` | Classic Outlook isn't installed, or you're on new Outlook. Use Option 2. |
| `The attempted operation failed. An object could not be found.` | Wrong `-Mailbox` or `-Folder` name. Mailbox is the name shown at the top of the folder pane. |
| Some items stay unread (Option 1) | Iterating `Items` directly while changing it skips items. The script copies the restricted set first. |
| Outlook shows a security prompt | Antivirus isn't recognised as up to date, so Outlook's object-model guard kicks in. |
| `403 Forbidden` / `ErrorAccessDenied` (Option 2) | Missing `Mail.ReadWrite` consent, or no access to that mailbox. |
| Read state comes back on another device | Wait for sync. Option 2 changes the server copy directly, so it wins. |

## References

- [Items.Restrict method (Outlook)](https://learn.microsoft.com/office/vba/api/outlook.items.restrict)
- [Update-MgUserMessage](https://learn.microsoft.com/powershell/module/microsoft.graph.mail/update-mgusermessage)
- [List messages - Microsoft Graph](https://learn.microsoft.com/graph/api/user-list-messages)
