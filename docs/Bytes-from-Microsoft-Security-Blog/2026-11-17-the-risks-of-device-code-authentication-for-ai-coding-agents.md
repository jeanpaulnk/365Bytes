---
title: "The risks of device code authentication for AI coding agents"
description: "Microsoft researchers explored the security risks of device code phishing targeting AI coding agents like GitHub Copilot CLI, demonstrating how attackers could abuse a phished authorization to remotely control sessions, read synced data, or access repositories. The article outlines detection capabil"
date: 2026-11-17
category: "Other"
source: "https://www.microsoft.com/en-us/security/blog/2026/11/17/the-risks-of-device-code-authentication-for-ai-coding-agents/"
---

# The risks of device code authentication for AI coding agents

*Published 17 November 2026*

## Summary

Microsoft researchers explored the security risks of device code phishing targeting AI coding agents like GitHub Copilot CLI, demonstrating how attackers could abuse a phished authorization to remotely control sessions, read synced data, or access repositories. The article outlines detection capabilities in Microsoft Defender and offers mitigation guidance such as reviewing OAuth grants and securing session settings.

## Key points

- Device code phishing tricks users into approving sign-in requests on legitimate sites initiated by attackers.
- Researchers simulated attacks using GitHub Copilot CLI to show potential risks like remote session steering, reading memory, and accessing private repositories.
- Microsoft Defender provides new detections to correlate phishing messages with unauthorized GitHub OAuth token creation.
- Organizations should educate users never to enter unsolicited device codes and to properly configure least-privilege access for AI tools.


[Read the full article on the Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/11/17/the-risks-of-device-code-authentication-for-ai-coding-agents/)

<small>This summary was written automatically with AI from the original article. Check the original for exact details before you act.</small>
