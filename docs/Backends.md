---
title: Backends
---

# Backends

Weebarr can send anime requests through either `Seerr` or `Sonarr Direct`.

You do not have to pick the "advanced" option to get started. The easiest way to think about it is:

- Choose `Seerr` if you already like your current Seerr request flow and want Weebarr to keep using it.
- Choose `Sonarr Direct` if you want Weebarr to add or update anime directly in Sonarr without going through Seerr.

You can switch later in **Settings**, so the choice is important but not permanent.

## What Changes When You Pick A Backend

The Seasonal page still looks and feels like Weebarr either way. What changes is the request path and the wording around availability.

### Seerr

When `Seerr` is selected:

- Weebarr keeps the current one-click request button.
- Clicking request sends the anime to Seerr.
- Seerr stays in charge of the downstream Sonarr request behavior.
- Weebarr shows Seerr-style states such as `Requested`, `Partially Available`, `Available`, `Season Missing`, and `No Seerr match`.

This is the better fit if Seerr is already where you manage request rules, approvals, or anime defaults.

### Sonarr Direct

When `Sonarr Direct` is selected:

- Weebarr opens a Sonarr-specific request modal instead of using the Seerr one-click action.
- The request goes straight to Sonarr.
- Weebarr uses Sonarr-native states such as `In Library`, `Partially Available`, `Available`, and `No Sonarr match`.
- The modal can choose seasons, monitor mode, search-on-add, and season-folder behavior.

This is the better fit if you want Weebarr to work more like a direct Sonarr companion instead of a Seerr front end.

## First-Run Setup

Weebarr setup now happens in two stages:

1. Configure access first.
2. Choose the request backend after auth is ready.

That means you do not land in the full app until Weebarr knows which request path you want to start with, unless you use `Skip Setup`.

## Seerr Setup

If you choose `Seerr`, the flow is simple:

1. Enter the Seerr base URL.
2. Enter the Seerr API key.
3. Pick the request-seasons preference if you want to change it.
4. Test the connection if needed.
5. Continue into the app.

In normal use, this keeps the familiar Weebarr behavior: click a title, review it, and use the existing Seerr request button.

## Sonarr Direct Setup

If you choose `Sonarr Direct`, the flow is a little more guided because Weebarr needs real Sonarr defaults before it can request cleanly.

1. Choose `http` or `https`.
2. Enter the Sonarr host.
3. Enter the port. `8989` is the normal default.
4. Paste the Sonarr API key.
5. Click `Validate Sonarr`.

After validation succeeds, Weebarr loads the live Sonarr-backed dropdowns for:

- root folder
- quality profile
- optional language profile

It also lets you save the normal Sonarr Direct defaults Weebarr should use later, including:

- series type
- monitor mode
- search-on-add
- season-folder behavior

The important part is that those dropdown values come from Sonarr itself. You are not expected to memorize profile IDs or folder IDs.

## Skip Setup

`Skip Setup` is there if you want to reach the app first and finish the backend config later.

That is useful when:

- you are still collecting the API key
- you are testing the UI remotely
- you want to finish auth first and come back to connections later

If you skip the backend step, Weebarr will still open, but request actions stay limited until the active backend is configured in **Settings**.

## Switching Later

You can switch between `Seerr` and `Sonarr Direct` later in **Settings**.

When you switch:

- Weebarr keeps the saved settings for both backends
- only one backend is active at a time
- the Seasonal page updates its status labels and request action to match the active backend

That means you can test Sonarr Direct without losing your Seerr settings, or go back to Seerr without rebuilding the Sonarr defaults from scratch.

## Which One Should Most People Use

Use `Seerr` if:

- your household already uses Seerr for requests
- you want the simplest path
- you want Weebarr to stay close to the older request flow

Use `Sonarr Direct` if:

- you mainly care about direct Sonarr control
- you want Sonarr-native season updates from inside Weebarr
- you want the request modal choices for monitor and search behavior

## Related Pages

- [Settings](Settings.md)
- [Features](Features.md)
- [Troubleshooting](Troubleshooting.md)
