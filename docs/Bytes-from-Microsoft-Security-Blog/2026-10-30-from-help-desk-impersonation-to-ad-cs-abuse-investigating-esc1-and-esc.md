---
title: "From help desk impersonation to AD CS abuse: Investigating ESC1 and ESC8 intrusion paths"
description: "Microsoft Threat Intelligence detailed human-operated intrusions where attackers used Microsoft Teams to impersonate IT help desks and trick users into granting remote access via Quick Assist. Once connected, attackers staged portable runtimes and exploited Active Directory Certificate Services (AD "
date: 2026-10-30
category: "Security update"
source: "https://www.microsoft.com/en-us/security/blog/2026/10/30/help-desk-impersonation-ad-cs-abuse-investigating-esc1-esc8-intrusion-paths/"
---

# From help desk impersonation to AD CS abuse: Investigating ESC1 and ESC8 intrusion paths

*Published 30 October 2026*

## Summary

Microsoft Threat Intelligence detailed human-operated intrusions where attackers used Microsoft Teams to impersonate IT help desks and trick users into granting remote access via Quick Assist. Once connected, attackers staged portable runtimes and exploited Active Directory Certificate Services (AD CS) vulnerabilities, specifically ESC1 and ESC8, to escalate privileges and compromise domain controllers.

## Key points

- Attackers used Microsoft Teams calls and messages to impersonate IT support and trick users into running Quick Assist.
- Portable runtimes (Python, Bun, Java) were deployed from user-writable directories to stage malicious payloads.
- Case 1 involved exploiting an ESC1-vulnerable certificate template to gain privileged credentials and perform DCSync.
- Case 2 utilized PetitPotam and ESC8 (NTLM relay to AD CS Web Enrollment) to acquire a domain controller certificate.
- Microsoft Defender attack disruptions mitigated much of the activity, though exclusions and unmitigated paths allowed some data exfiltration.


!!! warning "Action required"
    Exchange and Active Directory administrators must audit AD CS configurations for ESC1 and ESC8 vulnerabilities and review security exclusions.

[Read the full article on the Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/10/30/help-desk-impersonation-ad-cs-abuse-investigating-esc1-esc8-intrusion-paths/)

<small>This summary was written automatically with AI from the original article. Check the original for exact details before you act.</small>
