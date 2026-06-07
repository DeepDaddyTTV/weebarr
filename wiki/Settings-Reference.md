# Settings Reference

## Tabs

The Settings page is organized into four tabs:

- `Weebarr`
- `Automation`
- `Authentication`
- `Connections`

## Weebarr Tab

The Weebarr tab controls app-level behavior.

### Theme Mode

Theme mode is browser-local.

Options:

- `Dark`
- `System`
- `Light`

This affects the current browser only.

### Named Theme

Named theme is instance-level.

Built-in options:

- `Neon Lights`
- `Monochrome`
- `Color Picker`

Imported themes also appear here after a successful import.

### Theme Import

Supported import methods:

- direct URL to a `theme.json`
- `.zip` file containing a valid `theme.json`

The importer only accepts validated token manifests, not raw CSS or scripts.

### Content Filter

Controls whether AniList adult-only titles are hidden.

Options:

- `Hide NSFW`
- `Show all`

### Strict Monitoring

Strict Monitoring changes how sequel seasons are classified.

When disabled:

- later seasons can count as partially available when the base show is already tracked in Seerr

When enabled:

- later seasons without explicit coverage can become `Season Missing`

## Automation Tab

The Automation tab controls seasonal auto-request behavior.

### Enabled Buckets

Each seasonal group can be enabled or disabled:

- `S-Tier`
- `Canon`
- `Bingeable`
- `Filler`

### Scan Cadence

Automation cadence is stored as:

- `Days`
- `Hours`

Rules:

- days range: `0-365`
- hours range: `0-23`
- `0 days / 0 hours` is invalid

### Scan Actions

Automation supports:

- `Save Automation`
- `Scan Now`

When enabling automation for the first time, Weebarr can optionally begin with the current season immediately.

### Automation Summary

The panel tracks:

- last scan time
- last processed season
- last processed year
- current cadence

## Authentication Tab

The Authentication tab manages single-admin access.

### Local Account

Local access uses:

- username
- password

Passwords must match confirmation and meet the minimum length rule enforced by the backend.

### Plex Auth

Plex auth can be used alone or alongside local auth.

When both are configured:

- either sign-in path can be used

## Connections Tab

The Connections tab controls Seerr integration.

### Required Inputs

- Seerr Base URL
- API Key

### Optional Overrides

- Request Seasons
- Sonarr Server ID
- Force Series Type
- Force Quality Profile
- Quality Profile ID
- Root Folder
- Language Profile ID
- Request User ID
- Tags

### Request Seasons

Controls how Weebarr resolves season-specific titles:

- `all`
- `first`
- `latest`

### Force Series Type

Use this only if you need to override Seerr's default anime series type.

Options:

- `Use Seerr default`
- `Standard`
- `Anime / Absolute`
- `Daily`

### Force Quality Profile

If enabled, a profile ID must be supplied.

If disabled:

- Weebarr uses Seerr's current anime/default request profile behavior

### Live Connection

The live connection summary shows the currently stored effective integration values.

## Persistence Model

Settings are persisted to the mounted Weebarr config volume as JSON.

Theme mode remains browser-local, but instance settings such as:

- named theme
- strict monitoring
- automation cadence
- Seerr overrides
- auth mode

are stored server-side.

