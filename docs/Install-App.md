---
title: Install as an App
---

# Install Weebarr as an App

Weebarr includes PWA support, which means supported mobile browsers can add it to your home screen like an app.

It is still your self-hosted Weebarr site underneath. Your phone needs to be able to reach the same URL you use in the browser, and live data still depends on your Weebarr container, Seerr, Sonarr, and network being available.

## Before You Start

Use the public or local URL that you normally open on your phone.

Good examples:

- `https://weebarr.example.com`
- `http://192.168.1.50:18080`
- `http://localhost:18080` only when browsing from the same device that runs Weebarr

If you expose Weebarr through a reverse proxy, Cloudflare Tunnel, or another remote-access layer, use the HTTPS URL from that setup. That gives mobile browsers the best chance of treating Weebarr as installable.

## iPhone and iPad

Use Safari for the most reliable iOS home-screen install.

1. Open Weebarr in Safari.
2. Sign in if needed.
3. Tap the Safari share button.
4. Choose **Add to Home Screen**.
5. Confirm the name, then tap **Add**.

After that, open Weebarr from the new home-screen icon. It will use the mobile app shell with the centered logo, compact top bar, and full-screen navigation drawer.

## Android

Chrome and Edge both support installing Weebarr from the browser menu.

1. Open Weebarr in Chrome or Edge.
2. Sign in if needed.
3. Open the browser menu.
4. Choose **Install app** or **Add to Home screen**.
5. Confirm the install.

If Android only offers a shortcut instead of an app install, the site may not be reachable over HTTPS or the browser may not have seen the PWA manifest yet. Refresh the page, confirm the URL is reachable, and try again.

## Tips

- Keep `WEEBARR_PUBLIC_URL` set to the real URL if you use Plex login or public access.
- Keep your `/config` volume mounted before updating the container so app settings and auth survive releases.
- If the app opens to an old version after an update, refresh the browser page once. The service worker should then pick up the latest assets.
- If you change icons or PWA metadata, mobile browsers may cache the old home-screen icon for a while.

## Not a Native Store App

The installed app is a browser-powered PWA, not an App Store or Play Store package. That is intentional: it keeps Weebarr self-hosted, easy to update, and tied to your own deployment.
