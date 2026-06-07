# Troubleshooting

## The UI says Seerr is not configured

Check:

- `SEERR_BASE_URL`
- `SEERR_API_KEY`
- whether the Seerr URL is reachable from inside the Weebarr container

Use the `Connections` tab test action first.

## A title shows `No Seerr match`

This means Weebarr could not confidently map the anime to a TV entry in Seerr/TMDb.

Possible reasons:

- title naming mismatch
- upstream metadata mismatch
- missing external ID mapping

## Requests are using the wrong profile, root folder, or series type

Check the `Connections` tab.

Important points:

- `Use Seerr default` means Weebarr follows Seerr's saved anime/default behavior
- forcing values in Weebarr overrides the request payload
- forcing the wrong series type can cause conflicts with Seerr's Sonarr configuration

## Force Series Type shows an error

Common cause:

- Seerr does not expose the expected anime series type metadata for the selected server

Best fallback:

- set the desired anime series type in Seerr
- leave Weebarr on `Use Seerr default`

## Automation is not requesting titles

Check:

- at least one automation bucket is enabled
- the cadence is valid
- the title is actually in `Missing` or `Season Missing`
- Seerr is configured

Automation intentionally skips:

- `Requested`
- `Partially Available`
- `Available`

## Theme import fails

Theme imports must be:

- a valid remote `theme.json`
- or a zip containing `theme.json`

Raw CSS, JS, or arbitrary assets are not supported as theme manifests.

## Plex login fails

Check:

- `WEEBARR_PUBLIC_URL` is set correctly
- the public URL matches the URL used for sign-in
- your reverse proxy or tunnel is forwarding to Weebarr correctly

## First-run setup is blocked remotely

That is expected unless one of these is true:

- setup is being done from a direct local/private-network connection
- a bootstrap token is configured and used

## Tooltips or overlays seem clipped

That is usually a frontend stacking or overflow issue.

If it is reproducible:

1. note the page
2. note the theme and mode
3. capture a screenshot
4. report the exact hovered element

## Health Check

The fastest service-level verification is:

```text
/api/health
```

It should return:

- app status
- current version
- whether Seerr is configured

