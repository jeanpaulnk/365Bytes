---
title: "Reject Direct Send now Generally Available in Exchange Online"
description: "Microsoft has announced the General Availability of 'Reject Direct Send' in Exchange Online, allowing organizations to block unauthenticated inbound mail that uses their own accepted domains. Additionally, the feature is now being enabled by default for all newly created tenants to improve baseline "
date: 2026-11-17
category: "New feature"
source: "https://techcommunity.microsoft.com/t5/exchange-team-blog/reject-direct-send-now-generally-available-in-exchange-online/ba-p/4573787"
---

# Reject Direct Send now Generally Available in Exchange Online

*Published 17 November 2026*

## Summary

Microsoft has announced the General Availability of 'Reject Direct Send' in Exchange Online, allowing organizations to block unauthenticated inbound mail that uses their own accepted domains. Additionally, the feature is now being enabled by default for all newly created tenants to improve baseline security. Administrators of existing tenants can review traffic via the newly available Change Optics Report and manually opt in using PowerShell.

## Key points

- Reject Direct Send is now Generally Available worldwide for Exchange Online tenants.
- The feature blocks unauthenticated messages sent anonymously using the organization's accepted domains.
- New tenants will have Reject Direct Send enabled by default with no option to disable it.
- The Change Optics Report is also Generally Available to help admins identify legitimate Direct Send traffic.
- Admins can enable the setting using PowerShell via Set-OrganizationConfig -RejectDirectSend $true.


!!! warning "Action required"
    Exchange Online administrators should review the Change Optics Report to identify legitimate Direct Send traffic, configure inbound connectors for valid senders, and optionally enable the setting for existing tenants.

[Read the full article on the Exchange Team Blog](https://techcommunity.microsoft.com/t5/exchange-team-blog/reject-direct-send-now-generally-available-in-exchange-online/ba-p/4573787)

<small>This summary was written automatically with AI from the original article. Check the original for exact details before you act.</small>
