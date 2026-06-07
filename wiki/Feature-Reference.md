# Feature Reference

## Seasonal Page

The Seasonal page is the main dashboard.

It provides:

- A season/year picker
- Refresh and manual automation scan actions
- Summary stats for:
  - anime this season
  - requestable titles
  - already requested/tracked titles
  - airing soon
- Filters for text search, status, season, and sort order
- Seasonal grouping buckets:
  - `S-Tier`
  - `Canon`
  - `Bingeable`
  - `Filler`

Each anime card can show:

- Poster art
- Rank pill
- Audio pill such as `EN Dub` or `EN Sub`
- Main title
- Alternate title
- Season label
- AniList score
- AniList popularity
- Next episode timing
- Availability state
- Request action or AniList link

## Expanded Detail View

On desktop, selecting a card opens the right-side spotlight panel.

On mobile, selecting a card expands it inline.

The detail view can show:

- Poster/banner art
- Rank and audio pills
- Title and subtitle
- Score and popularity
- Genres
- Trailer embed
- Season summary
- Next airing data
- Audio state
- Overview
- Start date
- Seerr match details
- Availability state
- Full cast and voice actor information from AniList

## Requests Page

The Requests page only shows requests made through Weebarr.

It is not a full Seerr request history mirror.

Each row shows:

- Poster
- Title and subtitle
- Short description
- Request date
- Air date
- Current Weebarr/Seerr status

## Availability States

Weebarr uses these states:

- `Available`
  - All required seasons are available in Seerr.
- `Partially Available`
  - The show exists in Seerr and required seasons are at least partly covered by availability or request state.
- `Requested`
  - A request exists, but there is not yet enough availability to promote the title to partial or full availability.
- `Missing`
  - No request or usable tracked presence exists yet.
- `Season Missing`
  - Used when strict monitoring is enabled and a later season is not explicitly covered.
- `No Seerr match`
  - Weebarr could not confidently map the title to Seerr/TMDb.

## Audio Badges

Weebarr uses a best-effort audio badge system.

Possible badges include:

- `EN Dub`
- `EN Sub`

The app uses:

- AniList origin metadata
- cached MAL/Jikan voice actor data when available

If English voice actor data is not found, Weebarr falls back to `EN Sub`.

## Request Behavior

Weebarr sends TV requests through Seerr.

Important behavior:

- Weebarr does not request directly into Sonarr.
- Seerr remains the request gatekeeper.
- By default, Weebarr uses Seerr's anime/default request settings.
- Optional overrides in Settings can force:
  - Sonarr server selection
  - quality profile
  - series type
  - root folder
  - language profile
  - request user
  - tags

## Automation

Automation lets you auto-request seasonal titles by bucket.

Buckets:

- `S-Tier`
- `Canon`
- `Bingeable`
- `Filler`

Rules:

- only `Missing` and `Season Missing` titles are requestable by automation
- already-requested or already-tracked titles are skipped
- scans can run:
  - manually
  - on a saved cadence

## Themes

Weebarr supports named themes.

Built-in themes:

- `Neon Lights`
- `Monochrome`
- `Color Picker`

It also supports imported community themes using validated token JSON packs.

## Authentication

Weebarr is designed as a single-admin app.

Supported sign-in modes:

- local account
- Plex auth
- both local and Plex

## Security Model

Weebarr supports:

- first-run setup protection
- public URL pinning for Plex callback behavior
- signed sessions
- optional automation API key
- limited API key scope
- rate limiting for setup/login/Plex auth starts

