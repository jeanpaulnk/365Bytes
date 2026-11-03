---
title: "EWS Deprecation Is Here \u2013 What This Means To You"
description: "Exchange Online now requires tenants with EWS enabled to specify permitted application IDs; enabling EWS alone is no longer enough. Microsoft has begun notifying and updating some tenants, while tenants already enabled are not scheduled for Microsoft-initiated changes until April 2027. Sovereign clo"
date: 2026-10-26
category: "Retirement"
source: "https://techcommunity.microsoft.com/t5/exchange-team-blog/ews-deprecation-is-here-what-this-means-to-you/ba-p/4561431"
---

# EWS Deprecation Is Here – What This Means To You

!!! info "From the Exchange Team Blog"
    Based on [this article](https://techcommunity.microsoft.com/t5/exchange-team-blog/ews-deprecation-is-here-what-this-means-to-you/ba-p/4561431) by The_Exchange_Team, published 26 October 2026.

## Summary

Exchange Online now requires tenants with EWS enabled to specify permitted application IDs; enabling EWS alone is no longer enough. Microsoft has begun notifying and updating some tenants, while tenants already enabled are not scheduled for Microsoft-initiated changes until April 2027. Sovereign cloud timelines are still pending.

## Key points

- For WW tenants, EWSAllowedAppIDs is required when EWSEnabled is True.
- Microsoft populated allow lists for some tenants on October 10–11; admins enabling EWS after October 11 must configure the list themselves.
- Tenants with both settings null will receive a seven-day Message Center warning before Microsoft populates the list based on recent usage and disables EWS.
- Only tenant admins can re-enable EWS if Microsoft disables it; setting changes can take up to 24 hours for the allow list and up to four hours for EWSEnabled.
- Some Microsoft apps still require their AppID to be allowed; keep supported Outlook clients updated and check app-specific guidance.


!!! warning "Action required"
    Exchange Online tenant admins in the WW cloud: review EWS usage and configure EWSAllowedAppIDs for apps that must retain access; monitor Message Center warnings and re-enable EWS if needed. Admins whose tenants already have EWSEnabled=True have until April 2027 before Microsoft-initiated changes. Update affected Outlook clients; sovereign cloud admins should watch for a separate timeline.

[Read the full article on the Exchange Team Blog](https://techcommunity.microsoft.com/t5/exchange-team-blog/ews-deprecation-is-here-what-this-means-to-you/ba-p/4561431)

<small>This summary was written automatically with AI from the original article. Check the original for exact details before you act.</small>
