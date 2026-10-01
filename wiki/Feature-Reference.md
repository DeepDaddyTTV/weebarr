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
- Backend link and match actions

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
- Active backend match details
- Availability state
- Full cast and voice actor information from AniList

## Backend Links and Manual Matches

Matched titles offer `Open in Seerr` or `Open in Sonarr` for the active backend. A Sonarr title already in your library opens its series page. A Sonarr catalog match that has not been added opens the add-series page.

If a title shows `No Seerr match` or `No Sonarr match`, use `Find match`:

1. Review or edit the search title. An alternate title can help when the backend uses a different name.
2. Search the active backend's catalog.
3. Compare each result's title, year, poster, overview, and library status when available.
4. Choose `Use match` on the correct series.

`Use match` saves the association and refreshes the title's backend status. It does not create a request or add a series. Use the separate request action when you are ready.

Use `Change match` if an automatic or saved match points to the wrong series. For a saved manual choice, `Reset match` clears the override and returns the title to automatic matching.

Manual choices survive restarts and updates in `/config/weebarr.json`. Each choice belongs to one AniList ID, backend, and server, so a choice for Seerr is separate from a choice for Sonarr or a different server.

## Requests Page

The Requests page only shows requests made through Weebarr.

It is not a full copy of your Seerr request history or Sonarr library history.

Each row shows:

- Poster
- Title and subtitle
- Short description
- Request date
- Air date
- Current Weebarr or backend status

## Availability States

Seerr uses these states:

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

Sonarr Direct uses:

- `Available`: target season coverage is sufficiently available.
- `Partially Available`: some target coverage exists.
- `In Library`: the series is tracked, but target coverage is not sufficiently available.
- `Missing`: the matched series is not in Sonarr yet and can be added.
- `No Sonarr match`: lookup did not produce a confident usable candidate.

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

Weebarr sends TV requests through the active backend.

- `Seerr` uses the one-click request flow and Seerr's anime/default settings unless overridden in Weebarr. Seerr controls downstream requests, approvals, and user rules.
- `Sonarr Direct` opens a request modal with season selection, monitor mode, search-on-add, and season-folder controls. It uses the Sonarr defaults saved in Weebarr.

Saving a manual match does not submit a request. The normal request action uses the saved association when you choose to request the title.

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

