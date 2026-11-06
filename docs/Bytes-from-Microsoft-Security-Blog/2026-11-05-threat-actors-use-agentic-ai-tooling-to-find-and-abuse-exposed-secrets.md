---
title: "Threat actors use agentic AI tooling to find and abuse exposed secrets"
description: "Microsoft Threat Intelligence has observed threat actors using agentic AI offensive frameworks to search public code repositories for exposed credentials and rapidly execute follow-on cloud attacks. These automated tools can scan repositories, adapt API calls on the fly, and compromise Azure and Mic"
date: 2026-11-05
category: "Action required"
source: "https://www.microsoft.com/en-us/security/blog/2026/11/05/threat-actors-use-agentic-ai-tooling-to-find-and-abuse-exposed-secrets/"
---

# Threat actors use agentic AI tooling to find and abuse exposed secrets

*Published 5 November 2026*

## Summary

Microsoft Threat Intelligence has observed threat actors using agentic AI offensive frameworks to search public code repositories for exposed credentials and rapidly execute follow-on cloud attacks. These automated tools can scan repositories, adapt API calls on the fly, and compromise Azure and Microsoft 365 environments within minutes. Organizations are urged to audit code repositories, rotate exposed secrets, and implement specific conditional access and monitoring controls.

## Key points

- Threat actors are using agentic AI frameworks to scale and accelerate the discovery of exposed secrets in public code repositories.
- Observed campaigns progressed from scanning GitHub to exfiltrating data and abusing Azure Key Vault and AI services in as little as five minutes.
- AI agents demonstrated adaptive behavior, automatically correcting outdated API versions and methods upon receiving HTTP error responses.
- Organizations must immediately revoke and rotate compromised credentials, review service principal sign-in logs, and block malicious IP addresses.


!!! warning "Action required"
    Cloud and security administrators must scan code repositories for exposed secrets, rotate affected credentials, block malicious IPs in Conditional Access policies, and review Entra service principal logs.

[Read the full article on the Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/11/05/threat-actors-use-agentic-ai-tooling-to-find-and-abuse-exposed-secrets/)

<small>This summary was written automatically with AI from the original article. Check the original for exact details before you act.</small>
