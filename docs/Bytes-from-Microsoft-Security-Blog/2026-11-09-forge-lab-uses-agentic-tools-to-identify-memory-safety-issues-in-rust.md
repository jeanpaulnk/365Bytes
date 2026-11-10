---
title: "FORGE Lab uses agentic tools to identify memory safety issues in Rust"
description: "Microsoft's FORGE Lab used an AI-powered vulnerability-scanning tool to discover memory safety issues and soundness bugs within Rust's standard library. The findings highlight three common patterns of misplaced trust in unsafe code: code not to panic, user-provided implementations, and the underlyin"
date: 2026-11-09
category: "Other"
source: "https://www.microsoft.com/en-us/security/blog/2026/11/09/forge-lab-uses-agentic-tools-to-identify-memory-safety-issues-in-rust/"
---

# FORGE Lab uses agentic tools to identify memory safety issues in Rust

*Published 9 November 2026*

## Summary

Microsoft's FORGE Lab used an AI-powered vulnerability-scanning tool to discover memory safety issues and soundness bugs within Rust's standard library. The findings highlight three common patterns of misplaced trust in unsafe code: code not to panic, user-provided implementations, and the underlying system. The research emphasizes the complexities of writing correct unsafe code even in memory-safe languages like Rust.

## Key points

- FORGE Lab used an AI tool called Hyenas to find memory safety bugs in Rust's standard library.
- Bugs were categorized into three patterns of misplaced trust in unsafe code.
- Panic safety issues occur when unwinding leaves broken invariants exposed.
- User-provided implementations can return incorrect data, leading to unsoundness if trusted blindly.


[Read the full article on the Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/11/09/forge-lab-uses-agentic-tools-to-identify-memory-safety-issues-in-rust/)

<small>This summary was written automatically with AI from the original article. Check the original for exact details before you act.</small>
