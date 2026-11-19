---
title: "Sending From Email Aliases \u2013 General Availability"
description: "Microsoft has announced the General Availability of Sending from Aliases for Exchange Online, allowing users to send and reply to emails using any of their secondary proxy addresses rather than just their primary SMTP address. Admins can enable this capability at the tenant level via the Exchange Ad"
date: 2026-11-18
category: "New feature"
source: "https://techcommunity.microsoft.com/t5/exchange-team-blog/sending-from-email-aliases-general-availability/ba-p/4562543"
---

# Sending From Email Aliases – General Availability

*Published 18 November 2026*

## Summary

Microsoft has announced the General Availability of Sending from Aliases for Exchange Online, allowing users to send and reply to emails using any of their secondary proxy addresses rather than just their primary SMTP address. Admins can enable this capability at the tenant level via the Exchange Admin Center or PowerShell, though certain limitations apply regarding hybrid environments, shared mailboxes, and message tracking.

## Key points

- Users can now send and reply to emails using configured proxy aliases in Exchange Online.
- Admins can enable the feature globally via PowerShell or the Exchange Admin Center.
- Includes options to restrict specific domains from sending using the Set-Accepteddomain cmdlet.
- Known limitations exist for shared mailboxes in Outlook desktop clients and hybrid routing scenarios.
- Message trace queries require the specific alias to track emails sent from secondary addresses.


!!! warning "Action required"
    Exchange administrators who want to enable the sending from aliases feature for their tenant can turn it on via the admin center or PowerShell.

[Read the full article on the Exchange Team Blog](https://techcommunity.microsoft.com/t5/exchange-team-blog/sending-from-email-aliases-general-availability/ba-p/4562543)

<small>This summary was written automatically with AI from the original article. Check the original for exact details before you act.</small>
