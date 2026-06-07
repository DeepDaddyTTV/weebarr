# API Reference

## Auth Model

Weebarr supports two broad API access patterns:

- authenticated browser session
- automation API key for safe API access

The automation API key is intentionally limited and should not be treated as a full admin token.

## Common Response Notes

- most JSON endpoints return standard FastAPI JSON payloads
- health and config routes are read-only
- settings mutation routes require an authenticated admin session

## UI Routes

### `GET /`

Redirects to the current starting page based on auth/setup state.

### `GET /setup`

First-run setup UI.

### `GET /login`

Login UI.

### `GET /logout`

Clears the active session.

### `GET /seasonal`

Seasonal dashboard UI.

### `GET /requests`

Weebarr-owned request history UI.

### `GET /settings`

Settings UI.

## Setup and Auth API

### `GET /api/setup/status`

Returns whether setup is still required.

### `POST /api/setup/access`

Completes first-run setup.

### `POST /api/auth/login`

Local username/password login.

### `GET /auth/plex/start`

Starts Plex auth.

### `GET /auth/plex/callback`

Plex auth callback.

## Read APIs

### `GET /api/health`

Health check.

Typical output:

- app status
- version
- whether Seerr is configured

### `GET /api/config`

Public runtime config used by the frontend.

Includes:

- current version
- default season/year
- season options
- Seerr summary
- Weebarr summary
- access summary

### `GET /api/settings/weebarr`

Current Weebarr settings summary.

### `GET /api/settings/seerr`

Current Seerr settings summary.

### `GET /api/seasonal`

Returns the seasonal anime payload.

Query params:

- `season`
- `year`
- `perPage`

### `GET /api/anime/{anime_id}/characters`

Returns AniList character and voice actor information for one anime.

## Mutation APIs

### `PUT /api/settings/access/local`

Creates or updates the local account.

### `PUT /api/settings/weebarr`

Saves Weebarr settings:

- content filter
- strict monitoring
- automation config
- theme config

### `POST /api/automation/scan`

Runs a manual automation scan.

Payload supports:

- `season`
- `year`
- `force`

### `POST /api/themes/import/url`

Imports a theme from a remote JSON manifest URL.

### `POST /api/themes/import/zip`

Imports a theme from a zip upload containing `theme.json`.

### `POST /api/settings/seerr/test`

Tests the supplied Seerr connection info without saving it.

### `PUT /api/settings/seerr`

Saves effective Seerr request settings and overrides.

### `POST /api/request`

Creates a Seerr TV request and records a Weebarr request entry when applicable.

## Automation API Key Access

Safe API-key use is intended for automation and external tooling.

Typical allowed use cases:

- health checks
- config reads
- seasonal reads
- character reads
- request creation

Do not assume the API key can manage:

- setup
- auth state
- settings writes

## Error Behavior

Common status codes:

- `200` or `201` for success
- `400` for invalid inputs
- `401` for missing or invalid auth
- `409` for already-requested cases
- `502` when an upstream metadata source fails
- `503` when Seerr is not configured

