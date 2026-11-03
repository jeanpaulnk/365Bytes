---
title: Microsoft 365 Message Center
description: Read Microsoft 365 Message Center, Microsoft 365 Roadmap and Azure Updates posts without signing in to the admin center.
---

# Microsoft 365 Message Center

Read Microsoft 365 Message Center, Microsoft 365 Roadmap and Azure Updates posts here, without signing in to the Microsoft 365 admin center. Every post also links to its source.

!!! info "Source"
    Posts come from the [Microsoft 365 Message Center Archive](https://mc.merill.net/) by Merill Fernando and are refreshed on this site every few hours.

<div class="mc-buttons">
  <a class="md-button md-button--primary" href="https://mc.merill.net/" target="_blank" rel="noopener">Browse the full archive</a>
  <a class="md-button" href="https://mc.merill.net/?source=messageCenter" target="_blank" rel="noopener">Message Center</a>
  <a class="md-button" href="https://mc.merill.net/?source=roadmap" target="_blank" rel="noopener">M365 Roadmap</a>
  <a class="md-button" href="https://mc.merill.net/?source=azure" target="_blank" rel="noopener">Azure Updates</a>
  <a class="md-button" href="https://mc.merill.net/rss.xml" target="_blank" rel="noopener">RSS</a>
</div>

## Go to a post or search

<form id="mc-go" class="mc-row">
  <input type="text" id="mc-go-input" class="mc-input" placeholder="MC1234567, RM570662, or words like Teams passkeys" aria-label="Post ID or search text">
  <button type="submit" class="md-button md-button--primary">Go</button>
</form>
<p class="mc-hint">An ID (MC…, RM…, AZ…) opens the post here. Anything else searches the full archive on mc.merill.net.</p>

## Latest posts

<div id="mc-latest">
  <div class="mc-tabs" role="group" aria-label="Filter by source">
    <button type="button" data-src="all" aria-pressed="true">All</button>
    <button type="button" data-src="messageCenter" aria-pressed="false">Message Center</button>
    <button type="button" data-src="roadmap" aria-pressed="false">Roadmap</button>
    <button type="button" data-src="azure" aria-pressed="false">Azure</button>
  </div>
  <input type="text" id="mc-filter" class="mc-input" placeholder="Filter by title, service or ID" aria-label="Filter posts">
  <p id="mc-status" class="mc-hint">Loading latest posts…</p>
  <ul id="mc-posts" class="mc-posts"></ul>
</div>

!!! warning "Tenant-specific"
    Message Center posts differ between tenants. Always check applicability and timing in your own Microsoft 365 admin center.
