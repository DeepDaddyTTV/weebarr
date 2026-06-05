# Security Policy

## Supported versions

Security fixes are applied to the current `main` branch and the most recent published container image.

## Reporting a vulnerability

Please do not open public issues for suspected security problems.

Use one of these private channels instead:

1. Open a GitHub Security Advisory for this repository, if enabled for your account.
2. If private advisories are unavailable, contact the maintainer directly and include:
   - a short summary of the issue
   - affected version or commit
   - reproduction steps
   - impact assessment
   - any suggested remediation

We will acknowledge good-faith reports as quickly as possible and work toward a fix before public disclosure.

## Deployment guidance

Weebarr is designed to run behind normal self-hosting edge controls. Even with the in-app protections:

- keep Weebarr behind authentication
- prefer a reverse proxy or tunnel over exposing the raw container port directly
- set `WEEBARR_PUBLIC_URL` for HTTPS/Plex/public deployments
- apply edge rate limiting and abuse controls at Cloudflare, your reverse proxy, or both
