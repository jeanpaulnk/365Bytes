---
title: "AI-driven, large-scale nation-state campaign using ARTEX enables supply chain compromise"
description: "Microsoft reports that the China-state aligned actor Storm-0940 used the agentic AI penetration testing framework ARTEX to automate attacks and achieve privileged cloud access via a ConnectWise supply chain compromise. The rapid, machine-speed attacks allowed the threat actor to bypass human respons"
date: 2026-10-21
category: "Action required"
source: "https://www.microsoft.com/en-us/security/blog/2026/10/21/storm-0940-uses-artex-agentic-ai-connectwise-supply-chain-compromise/"
---

# AI-driven, large-scale nation-state campaign using ARTEX enables supply chain compromise

!!! info "From the Microsoft Security Blog"
    Based on [this article](https://www.microsoft.com/en-us/security/blog/2026/10/21/storm-0940-uses-artex-agentic-ai-connectwise-supply-chain-compromise/) by Microsoft Security Research and Microsoft Threat Intelligence, published 21 October 2026.

## Summary

Microsoft reports that the China-state aligned actor Storm-0940 used the agentic AI penetration testing framework ARTEX to automate attacks and achieve privileged cloud access via a ConnectWise supply chain compromise. The rapid, machine-speed attacks allowed the threat actor to bypass human response times, conducting reconnaissance, credential changes, and persistence mechanisms. Organizations must immediately inventory affected applications, review Microsoft Entra and M365 audit logs, and follow specific containment guidance.

## Key points

- Storm-0940 utilized the ARTEX agentic AI framework to scale and accelerate supply chain attacks globally.
- The campaign leveraged compromised ConnectWise cloud backup applications to gain unauthenticated access to Microsoft 365 tenants.
- AI agents rapidly performed reconnaissance, credential additions, and privilege modifications within hours of initial targeting.
- Microsoft urges administrators to keep affected ConnectWise integrations disabled and preserve evidence before making changes.
- Tenants must thoroughly review service-principal sign-ins, audit logs, and application permissions for suspicious modifications.


!!! warning "Action required"
    Microsoft 365 and Exchange administrators using ConnectWise cloud backup applications must immediately disable the integration, preserve logs, inventory specified application IDs, and review Entra ID and M365 audit records for unauthorized changes.

[Read the full article on the Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/10/21/storm-0940-uses-artex-agentic-ai-connectwise-supply-chain-compromise/){ .md-button .md-button--primary }

<small>This summary was written automatically with AI (Google Gemini, gemini-flash-lite-latest) from the original article. Check the original for exact details before you act.</small>
