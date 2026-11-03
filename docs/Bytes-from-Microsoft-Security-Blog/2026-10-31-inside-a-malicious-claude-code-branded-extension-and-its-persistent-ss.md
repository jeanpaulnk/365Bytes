---
title: "Inside a malicious Claude Code-branded extension and its persistent SSH backdoor"
description: "A malicious copy of the Claude Code extension was briefly distributed via the Cursor marketplace, executing a loader that added unauthorized SSH keys, established reverse SSH tunnels, and configured platform-specific persistence. Administrators must identify affected systems, remove malicious artifa"
date: 2026-10-31
category: "Action required"
source: "https://www.microsoft.com/en-us/security/blog/2026/10/30/inside-malicious-claude-code-branded-cursor-extension-persistent-ssh-backdoor/"
---

# Inside a malicious Claude Code-branded extension and its persistent SSH backdoor

*Published 31 October 2026*

## Summary

A malicious copy of the Claude Code extension was briefly distributed via the Cursor marketplace, executing a loader that added unauthorized SSH keys, established reverse SSH tunnels, and configured platform-specific persistence. Administrators must identify affected systems, remove malicious artifacts and persistence mechanisms, and review telemetry for unauthorized access.

## Key points

- A tampered Claude Code extension version was served on the Cursor marketplace for a limited time.
- The injected loader collected host information and environment variable names.
- The malware attempted to enable local SSH services, add rogue SSH keys, and set up reverse tunnels.
- Platform-specific persistence mechanisms were deployed via LaunchAgents, cron jobs, or scheduled tasks.
- Action is required to hunt for indicators, remove malicious persistence artifacts, and clean authorized_keys files.


!!! warning "Action required"
    Security and endpoint administrators using the Cursor marketplace must identify affected hosts, remove malicious SSH keys and persistence scripts, and rotate compromised credentials.

[Read the full article on the Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/10/30/inside-malicious-claude-code-branded-cursor-extension-persistent-ssh-backdoor/)

<small>This summary was written automatically with AI from the original article. Check the original for exact details before you act.</small>
