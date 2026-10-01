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
- active request backend
- whether the active request backend is configured
- whether Seerr is configured

### `GET /api/config`

Public runtime config used by the frontend.

Includes:

- current version
- default season/year
- season options
- request backend summary
- Weebarr summary
- access summary

### `GET /api/update-status`

Returns the published-container update status used by the sidebar warning card.

Includes:

- current running version
- latest published Docker Hub version
- whether the running container is outdated
- the update guide URL
- the version source

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

### `GET /api/matches/search`

Searches the active backend's TV catalog for manual match candidates.

Query parameters:

- `query`: the title to search
- `backend`: `seerr` or `sonarr`; it must match the current configured backend

Example:

```text
/api/matches/search?query=Blue%20Exorcist&backend=sonarr
```

Returns `backend` and a `results` array. Each result includes:

- `mediaId`: the backend catalog ID used when saving the match
- `title`
- `year`
- `overview`
- `posterUrl`
- `externalUrl`: a link to the backend's detail or add-series page
- `inLibrary`: whether the candidate is already in the backend's library

This route requires an authenticated admin session. Search does not save a choice or create a request.

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

### `PUT /api/anime/{anime_id}/match`

Saves a manual association for an AniList anime ID in the active backend.

Payload:

```json
{
  "backend": "sonarr",
  "mediaId": 12345
}
```

Use a `mediaId` returned by match search. `backend` accepts `seerr` or `sonarr` and must match the current configured backend.

Returns `success`, `backend`, and the refreshed `requestState`. The association is persisted in `/config/weebarr.json` for the AniList ID, backend, and server. Saving does not request the title or add it to Sonarr.

### `DELETE /api/anime/{anime_id}/match`

Clears the saved manual association for the current backend and server, then returns to automatic matching.

Supply `backend=seerr` or `backend=sonarr` in the query string. The backend must be current and configured.

Returns `success`, `backend`, and the refreshed `requestState`.

Both match mutation routes require an authenticated admin session. The automation API key cannot save or reset manual choices.

Match routes return `409` if the chosen backend is inactive or the configured server changes during lookup, `503` if the active backend is unconfigured, `404` if the anime or backend catalog entry cannot be found, and `502` if the upstream lookup fails. A whitespace-only search query returns `400`; invalid backend values or media IDs return `422`. Missing authentication returns `401`, and automation-API-key-only access returns `403`.

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
- manual match search, save, or reset

## Error Behavior

Common status codes:

- `200` or `201` for success
- `400` for invalid inputs
- `401` for missing or invalid auth
- `403` for credentials without access to the route
- `404` for an anime or backend catalog entry not found
- `409` for already-requested cases or backend/server conflicts
- `422` for input validation failures
- `502` when an upstream metadata source fails
- `503` when the active request backend is not configured
