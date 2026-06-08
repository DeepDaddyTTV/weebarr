---
title: Troubleshooting
---

# Troubleshooting

Start here when Weebarr is running, but something does not connect, request, import, log in, or display correctly.

When troubleshooting, change one thing at a time. Tiny steps beat button-mashing the server into soup.

## Quick Health Check

Open this in your browser:

```text
/api/health
```

For example, if Weebarr is running locally:

```text
http://localhost:18080/api/health
```

The health check should show:

- app status
- current version
- whether Seerr is configured

If this does not load, Weebarr itself may not be reachable yet.

## The UI Says Seerr Is Not Configured

This usually means Weebarr does not have working Seerr connection details saved.

Check:

- `SEERR_BASE_URL`
- `SEERR_API_KEY`
- whether Seerr is reachable from inside the Weebarr container

Go to **Settings** → **Connections** and use the connection test first.

### Common Cause

The Seerr URL works from your browser, but not from inside Docker.

If Seerr is also in Docker, try using the Docker service name:

```text
http://seerr:5055
```

If Seerr is outside Docker, use a URL the container can reach.

## A Title Shows `No Seerr match`

This means Weebarr could not confidently match the anime to a TV entry in Seerr or TMDb.

Common reasons:

- the anime title does not match cleanly
- Seerr or TMDb metadata is different from AniList metadata
- an external ID is missing or wrong
- the show exists under a different name

This does not always mean Weebarr is broken. Sometimes anime metadata is just a maze with wallpaper.

## Requests Use the Wrong Profile, Root Folder, or Series Type

Go to **Settings** → **Connections**.

Check whether you are forcing any request values.

Important behavior:

- `Use Seerr default` means Weebarr follows Seerr's saved anime/default behavior.
- Forced values in Weebarr override what gets sent in the request payload.
- Forcing the wrong series type can conflict with your Seerr or Sonarr setup.

For most users, the safest fix is:

1. Set the desired anime defaults in Seerr.
2. Leave Weebarr on `Use Seerr default`.
3. Test a request again.

## Force Series Type Shows an Error

This can happen when Seerr does not expose the expected anime series type metadata for the selected Sonarr server.

Best fallback:

1. Set the desired anime series type in Seerr.
2. In Weebarr, choose `Use Seerr default`.
3. Save and test again.

Only force series type in Weebarr if you know your Seerr or Sonarr setup needs it.

## Automation Is Not Requesting Titles

Check these first:

- at least one automation bucket is enabled
- the cadence is valid
- Seerr is configured
- the title is actually `Missing` or `Season Missing`

Automation intentionally skips:

- `Requested`
- `Partially Available`
- `Available`

That skip behavior prevents duplicate or unnecessary requests.

### Test Automation Manually

Go to the Seasonal page and run a manual automation scan.

If manual scan works but scheduled scan does not, check the cadence settings in **Settings** → **Automation**.

## Theme Import Fails

Theme imports must be one of these:

- a direct remote `theme.json`
- a `.zip` file containing `theme.json`

Weebarr does not support importing raw CSS, JavaScript, or random asset folders as themes.

If an import fails, confirm:

- the file is valid JSON
- the file is named `theme.json`
- the zip contains `theme.json`
- the URL points directly to the theme manifest

Use the [Theme Template](Theme-Template.md) page as your reference shape.

## Plex Login Fails

Check:

- `WEEBARR_PUBLIC_URL` is set correctly
- the public URL matches the address used during sign-in
- your reverse proxy or tunnel forwards to Weebarr correctly
- HTTPS is working if you are using a public address

If you recently changed domains, update `WEEBARR_PUBLIC_URL` and restart the container.

## First-Run Setup Is Blocked Remotely

This is expected unless one of these is true:

- setup is being done from a direct local or private-network connection
- a bootstrap token is configured and used

This protection helps prevent someone else from claiming your new Weebarr instance from the public internet.

Recommended approach:

1. Complete first-run setup locally.
2. Confirm login works.
3. Then expose Weebarr publicly if needed.

## API Key Was Exposed

If the automation API key was posted in a screenshot, log, script, or repo:

1. Open **Settings** → **API**
2. Regenerate the key
3. Update any scripts or integrations that use it

The old key stops working after regeneration.

## Tooltips or Overlays Look Clipped

This is usually a frontend layout issue involving stacking or overflow.

If you report it, include:

1. the page you were on
2. the theme and light/dark mode
3. a screenshot
4. the exact item you hovered or clicked
5. your browser and device type

That makes it much easier to reproduce.

## After an Update, Settings Are Gone

This usually means the config folder was not mounted correctly or the container was started with a different config path.

Check your compose file for:

```yaml
volumes:
  - ./config:/config
```

Then confirm you are starting Weebarr from the expected folder.

Your config folder should be backed up before updates.

## Still Stuck?

Collect these details before asking for help:

- your deployment type, such as Docker Desktop, Docker Engine, or Portainer
- your compose file with secrets removed
- Weebarr version
- whether Seerr is in Docker or outside Docker
- what `/api/health` returns
- the exact error message
- what you already tried

Redact API keys, tokens, public secrets, and private URLs before sharing logs or config.
