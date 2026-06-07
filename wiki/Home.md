# Weebarr Wiki

This wiki is the repo-side reference set for Weebarr. It is meant to explain what the app does, how to deploy it, how each settings area behaves, and what the API surface looks like.

## Pages

- [Feature Reference](Feature-Reference.md)
- [Settings Reference](Settings-Reference.md)
- [API Reference](API-Reference.md)
- [Docker Desktop on Windows](Deployment-Docker-Desktop-Windows.md)
- [Docker Desktop on Linux](Deployment-Docker-Desktop-Linux.md)
- [Other Deployment Options](Deployment-Other-Options.md)
- [Troubleshooting](Troubleshooting.md)

## What Weebarr Is

Weebarr is a seasonal anime dashboard for self-hosted libraries. It combines:

- AniList seasonal metadata
- Seerr request and availability state
- Sonarr-aware anime request defaults through Seerr
- Single-admin access with local auth, Plex auth, or both
- Theming and automation for recurring seasonal workflows

## Core Concepts

- `Seasonal`: Browse seasonal anime grouped into `S-Tier`, `Canon`, `Bingeable`, and `Filler`.
- `Requests`: See only requests created through Weebarr.
- `Settings`: Configure Weebarr behavior, automation, authentication, and Seerr integration.
- `Availability`: Weebarr classifies anime as `Available`, `Partially Available`, `Requested`, `Missing`, `Season Missing`, or `No Seerr match`.
- `Automation`: Optionally auto-request selected seasonal buckets on a schedule.

## Recommended Reading Order

1. [Feature Reference](Feature-Reference.md)
2. [Settings Reference](Settings-Reference.md)
3. One deployment guide:
   - [Docker Desktop on Windows](Deployment-Docker-Desktop-Windows.md)
   - [Docker Desktop on Linux](Deployment-Docker-Desktop-Linux.md)
   - [Other Deployment Options](Deployment-Other-Options.md)
4. [Troubleshooting](Troubleshooting.md)

