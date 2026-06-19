# Backends

Weebarr can work with either `Seerr` or `Sonarr Direct`.

The short version:

- choose `Seerr` if you want Weebarr to keep the familiar one-click request flow
- choose `Sonarr Direct` if you want Weebarr to add or update anime directly in Sonarr

You can switch later in **Settings**, so this is a workflow choice, not a permanent lock-in.

## Seerr

When `Seerr` is active:

- Weebarr forwards the request through Seerr
- Seerr remains the request gatekeeper
- the Seasonal page shows Seerr-style availability states

This is the best fit if your existing stack already revolves around Seerr.

## Sonarr Direct

When `Sonarr Direct` is active:

- Weebarr opens a Sonarr-specific request modal
- the request goes directly to Sonarr
- the Seasonal page shows Sonarr-native availability states

This is the best fit if you want Weebarr to behave more like a direct Sonarr companion.

## Setup Flow

First-run setup now happens in two stages:

1. configure access
2. choose and configure the request backend

### Seerr setup

Seerr setup is the simple path:

1. enter the Seerr base URL
2. enter the Seerr API key
3. optionally choose request-season behavior
4. continue into the app

### Sonarr Direct setup

Sonarr Direct asks for a little more because Weebarr wants real Sonarr defaults instead of raw IDs:

1. choose `http` or `https`
2. enter the Sonarr host
3. enter the port, usually `8989`
4. paste the Sonarr API key
5. validate Sonarr

After validation, Weebarr loads the live Sonarr-backed dropdowns for:

- root folder
- quality profile
- optional language profile

It also saves the normal Sonarr Direct request defaults, including monitor mode, search-on-add, season-folder behavior, and series type.

## Skip Setup

`Skip Setup` lets you reach the main app before the backend is ready.

That is useful when you:

- need to come back with the API key later
- are testing remotely
- want to finish auth first and backend config second

## Switching Later

You can switch backends later in **Settings**. Weebarr keeps both saved configs, but only one backend is active at a time.

## Related Pages

- [Feature Reference](Feature-Reference.md)
- [Settings Reference](Settings-Reference.md)
- [Troubleshooting](Troubleshooting.md)
