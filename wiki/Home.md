# Weebarr Wiki

This wiki is the repo-side reference set for Weebarr. It is meant to explain what the app does, how to deploy it, how each settings area behaves, and what the API surface looks like.

## Pages

- [Backends](Backends.md)
- [Feature Reference](Feature-Reference.md)
- [Settings Reference](Settings-Reference.md)
- [API Reference](API-Reference.md)
- [Docker Desktop on Windows](Deployment-Docker-Desktop-Windows.md)
- [Docker Desktop on Linux](Deployment-Docker-Desktop-Linux.md)
- [Other Deployment Options](Deployment-Other-Options.md)
- [Update Container](Update-Container.md)
- [Troubleshooting](Troubleshooting.md)

## What Weebarr Is

Weebarr is a seasonal anime dashboard for self-hosted libraries. It combines:

- AniList seasonal metadata
- Request and availability state from either Seerr or Sonarr Direct
- Backend-specific request controls that still fit the same Weebarr workflow
- Single-admin access with local auth, Plex auth, or both
- Theming and automation for recurring seasonal workflows

## Core Concepts

- `Seasonal`: Browse seasonal anime grouped into `S-Tier`, `Canon`, `Bingeable`, and `Filler`.
- `Requests`: See only requests created through Weebarr.
- `Backends`: Choose the Seerr flow or the Sonarr Direct flow and understand what each one changes.
- `Settings`: Configure Weebarr behavior, automation, authentication, and request-backend settings.
- `Availability`: Weebarr classifies anime with backend-aware states such as `Available`, `Partially Available`, `Requested`, `In Library`, `Missing`, `Season Missing`, `No Seerr match`, or `No Sonarr match`.
- `Automation`: Optionally auto-request selected seasonal buckets on a schedule.

## Recommended Reading Order

1. [Backends](Backends.md)
2. [Feature Reference](Feature-Reference.md)
3. [Settings Reference](Settings-Reference.md)
4. One deployment guide:
   - [Docker Desktop on Windows](Deployment-Docker-Desktop-Windows.md)
   - [Docker Desktop on Linux](Deployment-Docker-Desktop-Linux.md)
   - [Other Deployment Options](Deployment-Other-Options.md)
   - [Update Container](Update-Container.md)
5. [Troubleshooting](Troubleshooting.md)
