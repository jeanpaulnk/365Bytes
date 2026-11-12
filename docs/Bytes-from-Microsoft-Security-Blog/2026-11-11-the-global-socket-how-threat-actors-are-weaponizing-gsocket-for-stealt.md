---
title: "The global socket: how threat actors are weaponizing GSocket for stealthy C2"
description: "Microsoft is tracking an increase in threat actors deploying the open-source GSocket tool on compromised Linux servers to maintain persistent, encrypted command and control access via public relay networks. Because GSocket operates independently of initial vulnerabilities and uses shared relay infra"
date: 2026-11-11
category: "Action required"
source: "https://www.microsoft.com/en-us/security/blog/2026/11/11/global-socket-how-threat-actors-weaponizing-gsocket-stealthy-c2/"
---

# The global socket: how threat actors are weaponizing GSocket for stealthy C2

*Published 11 November 2026*

## Summary

Microsoft is tracking an increase in threat actors deploying the open-source GSocket tool on compromised Linux servers to maintain persistent, encrypted command and control access via public relay networks. Because GSocket operates independently of initial vulnerabilities and uses shared relay infrastructure instead of fixed IP addresses, patching web applications alone is insufficient. Administrators must actively hunt for persistence mechanisms, inspect outbound traffic, and remediate both the initial compromise and the deployed tooling.

## Key points

- Threat actors use GSocket to maintain persistent, stealthy access on compromised Linux servers after initial web application vulnerabilities are patched.
- GSocket relies on shared public relay infrastructure and a shared secret rather than fixed C2 IP addresses, making traditional IP blocking ineffective.
- Telemetry shows a 356.2% increase in GSocket-related detections, heavily impacting web applications, PHP environments, and Apache servers.
- Remediation requires comprehensive investigation of the host, including removing GSocket binaries, auditing persistence mechanisms (cron, systemd), and enforcing strict egress filtering.


!!! warning "Action required"
    Linux administrators and security teams must audit internet-facing web servers for GSocket tooling, inspect persistence surfaces, implement strict outbound egress filtering, and ensure both application vulnerabilities and local privilege escalation paths are patched.

[Read the full article on the Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/11/11/global-socket-how-threat-actors-weaponizing-gsocket-stealthy-c2/)

<small>This summary was written automatically with AI from the original article. Check the original for exact details before you act.</small>
