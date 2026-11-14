---
title: "SCKit abuses ScreenConnect to deploy remote access and target technician sessions"
description: "Microsoft is tracking an active campaign where threat actors abuse legitimate ConnectWise ScreenConnect instances to install unauthorized remote-access clients and deploy the SCKit malware worm. The toolkit establishes persistence, steals browser cookies for authentication sessions, and targets IT s"
date: 2026-11-13
category: "Security update"
source: "https://www.microsoft.com/en-us/security/blog/2026/11/13/sckit-abuses-screenconnect-deploy-remote-access-target-technician-sessions/"
---

# SCKit abuses ScreenConnect to deploy remote access and target technician sessions

*Published 13 November 2026*

## Summary

Microsoft is tracking an active campaign where threat actors abuse legitimate ConnectWise ScreenConnect instances to install unauthorized remote-access clients and deploy the SCKit malware worm. The toolkit establishes persistence, steals browser cookies for authentication sessions, and targets IT support technicians to propagate payloads to downstream endpoints. Defenders are advised to investigate technician workstations and managed endpoints for indicators of compromise.

## Key points

- Threat actors are abusing ConnectWise ScreenConnect to deploy the SCKit worm on MSP and customer endpoints.
- SCKit establishes persistence via scheduled tasks and registry keys, and creates unauthorized remote-access channels.
- The toolkit targets IT support technician workstations and browser authentication cookies to spread payloads.
- Microsoft provides advanced hunting queries and mitigation guidance to detect and disrupt this campaign.


!!! warning "Action required"
    Administrators managing ConnectWise ScreenConnect instances must investigate technician workstations and downstream endpoints, review access permissions, and apply vendor mitigations.

[Read the full article on the Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/11/13/sckit-abuses-screenconnect-deploy-remote-access-target-technician-sessions/)

<small>This summary was written automatically with AI from the original article. Check the original for exact details before you act.</small>
