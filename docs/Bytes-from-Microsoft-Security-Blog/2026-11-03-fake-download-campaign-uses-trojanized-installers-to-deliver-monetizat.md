---
title: "Fake-download campaign uses trojanized installers to deliver monetization payloads"
description: "Microsoft has identified a fake-download campaign using trojanized Inno Setup installers to distribute unauthorized monetization payloads, such as proxyware, distributed-computing platforms, and adware. These bundles are typically hidden within cracked software, game installers, and unofficial utili"
date: 2026-11-03
category: "Security update"
source: "https://www.microsoft.com/en-us/security/blog/2026/11/03/fake-download-campaign-uses-trojanized-installers-deliver-monetization-payloads/"
---

# Fake-download campaign uses trojanized installers to deliver monetization payloads

*Published 3 November 2026*

## Summary

Microsoft has identified a fake-download campaign using trojanized Inno Setup installers to distribute unauthorized monetization payloads, such as proxyware, distributed-computing platforms, and adware. These bundles are typically hidden within cracked software, game installers, and unofficial utilities. Organizations are advised to block untrusted software sources, enable reputation-based protection, and monitor for unauthorized persistence mechanisms.

## Key points

- Campaign targets users searching for cracked software, activators, and free games with fake Inno Setup installers.
- Installers use a callback mechanism to deploy multiple downstream monetization payloads during a single session.
- Identified monetization branches include WorldProxyPool (proxyware), CharityEngine/BOINC (compute-resource sharing), and AW Manager (adware).
- Attackers utilize scheduled tasks and unattended installation switches to establish persistence and evade user notice.
- Mitigations include enabling cloud-delivered protection, tamper protection, and reputation-based security settings in Microsoft Defender.


!!! warning "Action required"
    Administrators should ensure Microsoft Defender cloud-delivered and reputation-based protections are enabled across organization endpoints to detect untrusted software and PUA installations.

[Read the full article on the Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/11/03/fake-download-campaign-uses-trojanized-installers-deliver-monetization-payloads/)

<small>This summary was written automatically with AI from the original article. Check the original for exact details before you act.</small>
