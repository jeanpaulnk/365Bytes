<#
.SYNOPSIS
    Marks all unread items in an Outlook folder as read.
.EXAMPLE
    .\Set-OutlookFolderRead.ps1 -Mailbox user@domain.com -Folder "Deleted Items"
.EXAMPLE
    .\Set-OutlookFolderRead.ps1 -Mailbox user@domain.com -Folder "Inbox\Projects" -Recurse -WhatIf
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)] [string]$Mailbox,   # display name of the store, usually the SMTP address
    [string]$Folder = "Inbox",                 # use \ for subfolders, e.g. "Inbox\Projects"
    [switch]$Recurse
)

$outlook   = New-Object -ComObject Outlook.Application
$namespace = $outlook.GetNamespace("MAPI")

# Resolve the folder path
$target = $namespace.Folders.Item($Mailbox)
foreach ($part in $Folder.Split('\')) { $target = $target.Folders.Item($part) }

function Set-FolderRead($f) {
    # Restrict returns only unread items; copy to an array so the
    # collection does not shrink while we change it
    $unread = @($f.Items.Restrict("[UnRead] = True"))
    if ($unread.Count -and $PSCmdlet.ShouldProcess($f.FolderPath, "Mark $($unread.Count) item(s) as read")) {
        foreach ($item in $unread) { $item.UnRead = $false; $item.Save() }
    }
    Write-Host ("{0,-50} {1,6} marked read" -f $f.FolderPath, $unread.Count)
    if ($Recurse) { foreach ($sub in $f.Folders) { Set-FolderRead $sub } }
}

Set-FolderRead $target
