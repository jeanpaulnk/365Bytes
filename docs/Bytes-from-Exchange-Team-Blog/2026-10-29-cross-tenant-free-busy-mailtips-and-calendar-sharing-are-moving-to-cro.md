---
title: "Cross-tenant Free/Busy, MailTips, and Calendar Sharing are moving to Cross-Tenant Access Policy"
description: "Exchange Online is moving cross-tenant Free/Busy, MailTips, and calendar sharing from EWS to Microsoft 365 Cross-Tenant Access Policy. Organizations that use the affected sharing configurations need to migrate after the new policy reaches both tenants; admins who need more time can keep EWS enabled "
date: 2026-10-29
category: "Retirement"
source: "https://techcommunity.microsoft.com/t5/exchange-team-blog/cross-tenant-free-busy-mailtips-and-calendar-sharing-are-moving/ba-p/4545169"
---

# Cross-tenant Free/Busy, MailTips, and Calendar Sharing are moving to Cross-Tenant Access Policy

!!! info "From the Exchange Team Blog"
    Based on [this article](https://techcommunity.microsoft.com/t5/exchange-team-blog/cross-tenant-free-busy-mailtips-and-calendar-sharing-are-moving/ba-p/4545169) by The_Exchange_Team, published 29 October 2026.

## Summary

Exchange Online is moving cross-tenant Free/Busy, MailTips, and calendar sharing from EWS to Microsoft 365 Cross-Tenant Access Policy. Organizations that use the affected sharing configurations need to migrate after the new policy reaches both tenants; admins who need more time can keep EWS enabled temporarily, through April 1, 2027.

## Key points

- Only cross-tenant sharing with Microsoft 365 organizations using affected Organization Relationships or Sharing Policies is in scope.
- Admins can use Exchange Online PowerShell checks in the post to confirm whether their tenant is affected.
- Migrate and validate the new policy after rollout reaches both organizations; the calendar-sharing rollout is expected to complete November 9, 2026 in Worldwide.
- Setting EWSEnabled to True can preserve existing sharing during migration; both tenants need it for bidirectional sharing.
- The extension ends April 1, 2027, when affected configurations must have moved off EWS.


!!! warning "Action required"
    Admins of organizations using affected cross-tenant sharing should confirm scope, migrate to Cross-Tenant Access Policy after rollout reaches both tenants, and finish by April 1, 2027. If migration is delayed, set EWSEnabled to True in both tenants for bidirectional sharing until migration is complete.

[Read the full article on the Exchange Team Blog](https://techcommunity.microsoft.com/t5/exchange-team-blog/cross-tenant-free-busy-mailtips-and-calendar-sharing-are-moving/ba-p/4545169){ .md-button .md-button--primary }

<small>This summary was written automatically with AI (GitHub Copilot or another model) from the original article. Check the original for exact details before you act.</small>
