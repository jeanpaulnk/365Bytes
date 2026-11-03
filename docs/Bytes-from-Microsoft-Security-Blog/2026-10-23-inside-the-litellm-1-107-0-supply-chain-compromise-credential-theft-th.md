---
title: "Inside the LiteLLM 1.107.0 supply chain compromise: Credential theft through Python startup hooks"
description: "A malicious version of the LiteLLM package was published to PyPI and container registries, utilizing Python startup mechanisms to automatically steal sensitive credentials. Simply launching the Python interpreter in an impacted environment triggered the payload even without importing LiteLLM. Organi"
date: 2026-10-23
category: "Action required"
source: "https://www.microsoft.com/en-us/security/blog/2026/10/23/inside-the-litellm-1-107-0-supply-chain-compromise-credential-theft-through-python-startup-hooks/"
---

# Inside the LiteLLM 1.107.0 supply chain compromise: Credential theft through Python startup hooks


## Summary

A malicious version of the LiteLLM package was published to PyPI and container registries, utilizing Python startup mechanisms to automatically steal sensitive credentials. Simply launching the Python interpreter in an impacted environment triggered the payload even without importing LiteLLM. Organizations must isolate systems, purge residual startup files, and rotate all exposed credentials.

## Key points

- LiteLLM 1.107.0 was compromised on PyPI and via official container images.
- Custom startup files (.pth and sitecustomize.py) executed malicious payloads automatically during Python initialization.
- The payload targeted developer tokens, cloud credentials, browser data, and environment variables.
- Merely deleting the application package leaves malicious startup files behind.
- Administrators must rotate all reachable credentials and API keys from a clean machine.


!!! warning "Action required"
    Administrators, developers, and security teams using LiteLLM 1.107.0 must isolate affected systems, remove residual startup files, and rotate all exposed credentials.

[Read the full article on the Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/10/23/inside-the-litellm-1-107-0-supply-chain-compromise-credential-theft-through-python-startup-hooks/)

<small>This summary was written automatically with AI from the original article. Check the original for exact details before you act.</small>
