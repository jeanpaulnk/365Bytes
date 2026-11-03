---
title: "Exchange servers may become unstable after installation of October 2026 Windows updates"
description: "Some Exchange servers may become unstable after installing the October 2026 Windows Server updates, causing OWA failures, growing mail queues, or DAG quorum problems. Microsoft advises keeping the security updates installed, adding a registry setting, rebooting, and monitoring for recurrence."
date: 2026-10-20
category: "Known issue"
source: "https://techcommunity.microsoft.com/t5/exchange-team-blog/exchange-servers-may-become-unstable-after-installation-of/ba-p/4565382"
---

# Exchange servers may become unstable after installation of October 2026 Windows updates


## Summary

Some Exchange servers may become unstable after installing the October 2026 Windows Server updates, causing OWA failures, growing mail queues, or DAG quorum problems. Microsoft advises keeping the security updates installed, adding a registry setting, rebooting, and monitoring for recurrence.

## Key points

- The issue may affect Exchange Server 2016, 2019, and Subscription Edition on impacted Windows Server versions.
- Symptoms can include OWA connection errors, delayed email, and DAG quorum failures.
- Microsoft says not to uninstall or delay the October Windows security updates.
- The recommended workaround is to set EpmapSavedContextCap to 65536 and reboot the Exchange server.
- Monitor servers after reboot; Microsoft has not seen a need to raise the limit further.


!!! warning "Action required"
    Administrators of Exchange servers on affected Windows Server versions should install the October 2026 Windows updates, apply the registry setting, reboot, and monitor for recurrence.

[Read the full article on the Exchange Team Blog](https://techcommunity.microsoft.com/t5/exchange-team-blog/exchange-servers-may-become-unstable-after-installation-of/ba-p/4565382)

<small>This summary was written automatically with AI from the original article. Check the original for exact details before you act.</small>
