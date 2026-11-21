---
title: "Demystifying macOS Platform SSO: How Apple and Microsoft Entra ID work together"
description: "This post explains the architecture, ownership boundaries, and authentication flows behind macOS Platform SSO integrated with Microsoft Entra ID. It clarifies the distinct roles of MDM, Apple's macOS, the Microsoft Enterprise SSO plug-in, and Microsoft Entra ID in managing credentials and device tru"
date: 2026-11-20
category: "Other"
source: "https://techcommunity.microsoft.com/t5/microsoft-entra-blog/demystifying-macos-platform-sso-how-apple-and-microsoft-entra-id/ba-p/4437423"
---

# Demystifying macOS Platform SSO: How Apple and Microsoft Entra ID work together

*Published 20 November 2026*

## Summary

This post explains the architecture, ownership boundaries, and authentication flows behind macOS Platform SSO integrated with Microsoft Entra ID. It clarifies the distinct roles of MDM, Apple's macOS, the Microsoft Enterprise SSO plug-in, and Microsoft Entra ID in managing credentials and device trust. Additionally, it addresses common misconceptions regarding PRT handling, authentication methods, and Kerberos SSO integration.

## Key points

- Details the division of responsibilities between Apple, Microsoft, MDM, and applications in macOS Platform SSO.
- Clarifies that device registration establishes trust, while SSO uses that trust to obtain and protect the Platform SSO PRT.
- Explains that applications never receive the Platform SSO PRT directly, maintaining application isolation.
- Outlines how different authentication methods \(Password, UserSecureEnclaveKey, SmartCard\) function within the shared architecture.


[Read the full article on the Microsoft Entra Blog](https://techcommunity.microsoft.com/t5/microsoft-entra-blog/demystifying-macos-platform-sso-how-apple-and-microsoft-entra-id/ba-p/4437423)

<small>This summary was written automatically with AI from the original article. Check the original for exact details before you act.</small>
