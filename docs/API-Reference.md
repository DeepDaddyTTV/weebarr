---
title: API Reference
---

# API Reference

This page is for users who want to connect Weebarr to health checks, scripts, dashboards, or automation tools.

If you only use the web interface, you probably do not need this page.

## Access Model

Weebarr has two main API access patterns:

- a normal authenticated browser session
- an automation API key for limited external access

The automation API key is intentionally limited. Do not treat it like a full admin token.

## General Notes

Most API routes return JSON.

Health and config routes are read-only. Settings changes require an authenticated admin session.

When writing scripts, expect normal HTTP status codes:

- `200` or `201`: success
- `400`: invalid input
- `401`: missing or invalid authentication
- `409`: already requested or conflict
- `502`: upstream metadata source failed
- `503`: the active request backend is not configured or unavailable

## UI Routes

These routes serve the normal Weebarr web pages.

### `GET /`

Redirects to the correct starting page based on setup and login state.

### `GET /setup`

Shows the first-run setup page.

### `GET /setup/backend`

Shows the request-backend setup page after access is configured.

This page now starts on a backend-choice screen, then branches into the matching Seerr or Sonarr Direct setup form.

If `Sonarr Direct` is selected, the form asks for the Sonarr scheme, host, port, and API key first, then loads the live Sonarr root-folder, quality-profile, and optional language-profile choices after validation.

### `GET /login`

Shows the login page.

### `GET /logout`

Logs out the active session.

### `GET /seasonal`

Shows the Seasonal dashboard.

### `GET /requests`

Shows requests created through Weebarr.

### `GET /settings`

Shows the Settings page.

## Setup and Login API

### `GET /api/setup/status`

Returns whether first-run setup is still required, plus the current request-backend setup state.

### `POST /api/setup/access`

Completes first-run access setup.

### `POST /api/setup/backend`

Completes the first-run backend setup step and marks backend onboarding complete.

Use this when you want to save a real Seerr or Sonarr Direct config during setup before entering the main app.

For Sonarr Direct, the normal UI flow is to validate the Sonarr connection block first so the dropdown-backed folder and profile values come from Sonarr itself.

### `POST /api/setup/backend/skip`

Marks backend onboarding complete without requiring a working backend connection yet.

This lets a user reach the main app and finish backend config later in **Settings**.

### `POST /api/auth/login`

Logs in with the local username and password.

### `GET /auth/plex/start`

Starts Plex login.

### `GET /auth/plex/callback`

Handles the Plex login callback.

## Read APIs

Read APIs are useful for dashboards, checks, and external tools.

### `GET /api/health`

Basic health check.

Typical output includes:

- app status
- version
- the active request backend
- whether the active request backend is configured
- whether Seerr is configured

Use this for uptime checks.

### `GET /api/config`

Returns public runtime config used by the frontend.

This can include:

- current version
- default season and year
- available season options
- request backend summary
- Weebarr summary
- access summary

### `GET /api/settings/weebarr`

Returns the current Weebarr settings summary.

### `GET /api/settings/seerr`

Returns the current Seerr settings summary.

### `GET /api/settings/requests`

Returns the active request backend summary plus the saved Seerr and Sonarr Direct settings.

### `GET /api/seasonal`

Returns seasonal anime data.

Supported query parameters:

- `season`
- `year`
- `perPage`

Example shape:

```text
/api/seasonal?season=WINTER&year=2026&perPage=50
```

### `GET /api/anime/{anime_id}/characters`

Returns AniList character and voice actor information for one anime.

Replace `{anime_id}` with the anime ID.

## Write APIs

These routes change something or trigger an action.

Most write routes require an authenticated admin session.

### `PUT /api/settings/access/local`

Creates or updates the local account.

### `POST /api/settings/access/api-key/regenerate`

Generates or rotates the automation API key.

The new full key is returned once in the response. After that, Weebarr only keeps a masked preview and a secure stored verifier.

### `PUT /api/settings/weebarr`

Saves Weebarr settings, including:

- content filter
- strict monitoring
- automation config
- theme config

### `POST /api/automation/scan`

Runs a manual automation scan.

Payload may include:

- `season`
- `year`
- `force`

### `POST /api/themes/import/url`

Imports a theme from a remote `theme.json` URL.

### `POST /api/themes/import/zip`

Imports a theme from a zip file containing `theme.json`.

### `POST /api/settings/seerr/test`

Tests Seerr connection settings without saving them.

### `PUT /api/settings/seerr`

Saves Seerr request settings and overrides.

### `POST /api/settings/requests/test`

Tests the currently selected request backend without saving changes.

This can test either:

- Seerr connection details
- Sonarr Direct connection details and detected defaults

When testing `Sonarr Direct`, the response also includes the live option lists the UI uses to populate:

- `rootFolders`
- `qualityProfiles`
- `languageProfiles`

### `PUT /api/settings/requests`

Saves the active request backend plus backend-specific settings.

### `POST /api/request`

Creates a request through the active backend and records a Weebarr request entry when applicable.

In Seerr mode, the existing request payload still works.

In Sonarr Direct mode, the payload can also include an `options` object with:

- `selectedSeasons`
- `monitorMode`
- `searchOnAdd`
- `seasonFolder`

## Automation API Key

The automation API key is intended for safer external use.

Typical uses include:

- health checks
- config reads
- seasonal reads
- character reads
- request creation

Do not assume the automation API key can manage:

- first-run setup
- auth state
- settings writes

Keep the key private. If you paste it into a public script, repo, issue, screenshot, or log, treat it as compromised and rotate it.

## Practical Starting Points

For monitoring, start with:

```text
/api/health
```

For seasonal data, start with:

```text
/api/seasonal
```

For API key management and connection testing, start with the **Settings** page instead of manually calling routes unless you are automating the flow.
