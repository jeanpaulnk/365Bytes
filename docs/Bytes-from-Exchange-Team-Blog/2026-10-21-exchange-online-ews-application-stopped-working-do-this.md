---
title: "Exchange Online EWS application stopped working? Do this."
description: "Microsoft explains how tenant administrators can temporarily restore Exchange Web Services (EWS) if applications stop working after EWS is disabled. This workaround will no longer be available starting in April 2027, so affected applications must be updated to versions that do not rely on EWS."
date: 2026-10-21
category: "Retirement"
source: "https://techcommunity.microsoft.com/t5/exchange-team-blog/exchange-online-ews-application-stopped-working-do-this/ba-p/4566215"
---

# Exchange Online EWS application stopped working? Do this.

!!! info "From the Exchange Team Blog"
    Based on [this article](https://techcommunity.microsoft.com/t5/exchange-team-blog/exchange-online-ews-application-stopped-working-do-this/ba-p/4566215) by The_Exchange_Team, published 21 October 2026.

## Summary

Microsoft explains how tenant administrators can temporarily restore Exchange Web Services (EWS) if applications stop working after EWS is disabled. This workaround will no longer be available starting in April 2027, so affected applications must be updated to versions that do not rely on EWS.

## Key points

- Check Message Center to confirm whether EWS was disabled in your tenant.
- Administrators can temporarily re-enable EWS through Baseline Security Mode or Exchange Online PowerShell.
- Restoring EWS usually takes under an hour, but may take up to four hours.
- Changes to the EWS application allow list can take 24 hours to apply.
- EWS re-enablement ends in April 2027; dependent apps must transition away from EWS.


!!! warning "Action required"
    Tenant administrators with EWS-dependent apps should restore EWS temporarily if needed; administrators, application owners, and vendors must move those apps off EWS before April 2027.

[Read the full article on the Exchange Team Blog](https://techcommunity.microsoft.com/t5/exchange-team-blog/exchange-online-ews-application-stopped-working-do-this/ba-p/4566215)

<small>This summary was written automatically with AI from the original article. Check the original for exact details before you act.</small>
