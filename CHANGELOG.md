# Changelog

All notable changes to Weebarr will be documented in this file.

## [0.1.22] - 2026-06-05

### Added

- Embedded AniList trailer playback in the seasonal spotlight and mobile inline detail panel whenever AniList exposes an embeddable YouTube or Dailymotion trailer for the selected anime.

### Fixed

- Carried the Settings and availability refresh forward into a production rollout version without the retired `WEEBARR_ADMIN_TOKEN` write gate.

## [0.1.21] - 2026-06-05

### Changed

- Rebuilt Settings into full-width `Weebarr`, `Authentication`, and `Connections` sections, with Weebarr-local controls for content filtering and the new `Strict Monitoring` behavior.
- Removed the extra `WEEBARR_ADMIN_TOKEN` write gate so authenticated local/Plex sessions are now the only requirement for saving and testing Settings.
- Renamed the popularity buckets on the seasonal page to `S-Tier`, `Canon`, `Bingeable`, and `Filler`.

### Fixed

- Reworked seasonal availability into `Missing`, `Requested`, `Partially Available`, `Available`, and strict-only `Season Missing` so sequel monitoring behaves the way Sonarr/Seerr actually do in practice.
- Moved the seasonal card dub chip below the poster/meta area, flattened the stat cards, and corrected the `Airing Soon` icon centering on Seasonal and Requests.
- Preserved Weebarr request history as a fallback signal for `Requested` when Seerr does not surface the open request cleanly in its media payload.

## [0.1.20] - 2026-06-05

### Fixed

- Replaced the live-text `weebarr-wordmark.svg` auth branding with a font-independent render-safe wordmark, so login and setup no longer fall back to the wrong browser font for the `eebarr` text.
- Updated local-account username placeholders to the generic `username` label across login, setup, and Settings.

## [0.1.19] - 2026-06-05

### Fixed

- Applied the new `Weebarr-Login.webp` artwork to the auth background with a dark neon scrim so the login and setup pages use the added image without sacrificing readability.
- Centered the login-page Weebarr wordmark and intro copy so the auth panel feels balanced instead of left-weighted.
- Re-verified that the live login screen serves the exact `src/web/static/img/weebarr-wordmark.svg` asset rather than a fallback logo file.

### Changed

- First-run setup is now restricted to local/private addresses instead of relying on a setup token, so the initial claim flow is only available from local or private-network hosts.
- Setup now offers a true either-or admin choice: create a local username/password account or claim the instance to a single Plex account.
- The main sidebar brand now uses the real Weebarr SVG wordmark instead of reconstructing the logo from a separate mark and text.
- Plex-first setups can now add a local username/password later from Settings without losing Plex sign-in, and login automatically offers both methods whenever both are configured.
- The home dashboard sidebar no longer exposes the signed-in identity card; it keeps only the connection card plus a neutral sign-out action.

### Fixed

- Removed the old auto-login behavior after local account creation; local setup now lands on `/login` so the configured auth mode is actually respected.
- Added a real Plex setup path to the first-run screen, including a one-time Plex account claim that persists the allowed admin identity.
- Updated the login screen so local auth shows only username/password while Plex-only auth shows only the Plex button, matching the configured mode.
- Clarified the Settings-page `Weebarr Admin Token` copy so it is no longer confused with a Seerr credential.

## [0.1.17] - 2026-06-05

### Changed

- Simplified Weebarr access control to a single-admin model: first-run setup now creates one local admin account, and the login screen always offers both username/password and Plex sign-in.
- Removed the mode picker, public URL prompt, and first-run API key generation from the setup UI so first-run setup stays focused on creating the admin account.

### Fixed

- Restored correct `hidden` behavior across auth/setup surfaces so the setup success panel and other hidden UI blocks no longer render before they are opened.
- Updated the auth, dashboard, and settings copy to match the single-admin scope instead of implying multi-user or immediate automation-key setup.
- Kept the seasonal `Hide Requested` toggle centered between the season quick filter and the `Filters` action while preserving the custom in-page dropdown treatment on Settings.

## [0.1.16] - 2026-06-05

### Added

- Added a guided first-run access flow that blocks the dashboard until you choose either a local account or Plex Auth.
- Added session-based UI authentication and optional app API key authentication for `/api/*`, including first-run generation of the automation key.
- Added dedicated login/setup surfaces that use the Weebarr visual language instead of exposing a raw browser auth prompt.

### Fixed

- Converted the Settings page dropdowns to the same in-page `ui-select` system used elsewhere in Weebarr, so `Request Seasons` and `Content Filter` no longer fall back to browser-native selects.
- Centered the `Hide Requested` control within the lane between the seasonal quick filter and the `Filters` button for a more balanced desktop layout.
- Declared `itsdangerous` as a runtime dependency so Starlette session support works in clean installs and containers.

## [0.1.15] - 2026-06-05

### Added

- Added a persisted `Hide NSFW` setting in the Weebarr Settings page so seasonal discovery can either hide AniList adult-only anime or show the full feed.

### Fixed

- Simplified content filtering to a two-state model: `hide_nsfw` now directly follows AniList's adult-only flag, and older `adult_only` config values are automatically treated as the same mode for backwards compatibility.
- Fixed the spotlight and inline-detail status chips so the bubble wraps the status text instead of stretching awkwardly across the whole detail value column.

## [0.1.14] - 2026-06-05

### Fixed

- Improved Seerr title scoring for spacing-insensitive anime names so collapsed titles like `MARRIAGETOXIN` correctly match spaced TMDb/Seerr titles like `Marriage Toxin`.
- Restored `MARRIAGETOXIN` from a false `No Seerr match` failure to a real requestable series mapping in the live seasonal feed.

## [0.1.13] - 2026-06-05

### Fixed

- Switched Seerr matching to prefer an AniList MAL ID -> `ids.moe` -> TMDb ID path before falling back to title search, which makes season matching much more durable for anime with awkward English naming.
- Fixed Seerr title-search requests by explicitly percent-encoding the query string so search fallbacks no longer silently fail on titles with spaces and other reserved characters.
- Reclassified partial target seasons as already tracked instead of requestable, so shows like `Re:ZERO ... Season 4` and `That Time I Got Reincarnated as a Slime Season 4` no longer show a bogus missing-season request button.
- Shortened the remaining partial-state request CTA copy from `Request Missing Seasons` to `Request Missing`.

### Changed

- The Requests page now renders as a Weebarr-owned request list instead of a generic Seerr status mirror.
- Weebarr now persists its own request history and only shows titles on the Requests page when the request was actually sent from Weebarr.
- Seasonal API responses now annotate each anime with any matching Weebarr request record so the UI can distinguish Weebarr-origin requests from anime that merely exist in Seerr.

## [0.1.12] - 2026-06-05

### Fixed

- Reworked the top seasonal stat cards into a tighter right-value layout so the numbers sit in a dedicated lane and the summary row no longer feels oversized.
- Centered the mobile season picker row and moved the refresh action onto its own line so the season/year selector stays visually balanced on narrow screens.
- Added rounded gradient hover outlines and glow treatments to the main brand lockup and seasonal anime cards for a consistent interactive state.
- Replaced the sidebar's text glyphs with flat inline icons, including a TV icon for Seasonal, a radar-style icon for Requests, and a matching 2D gear for Settings.

### Changed

- README now embeds the transparent original Weebarr wordmark and the two manual dashboard captures placed in `src/web/static/img`.

## [0.1.11] - 2026-06-05

### Fixed

- Switched Seerr matching to resolve against the show itself while still preserving season-specific labels like `Season 4`, which prevents false non-matches on sequel anime.
- Made Seerr state classification season-aware so already requested titles like `Witch Hat Atelier` no longer show up as missing, while true sequel gaps like `Re:ZERO ... Season 4` stay requestable as missing specific seasons.
- Converted request season modes such as `all`, `first`, and `latest` into real season-number lists before calling Seerr, so those settings are genuinely usable in live requests.
- Reworked the seasonal card footer so requested/requestable actions are real standalone controls instead of being nested inside the card trigger.
- Replaced the stat-card glyph text icons with centered CSS-drawn icons and kept the metric lane alignment consistent across the top summary row.

### Changed

- The seasonal cards and spotlight now surface franchise installment labels alongside the airing season window, for example `Season 4 • Spring 2026`.
- README now uses the real Weebarr wordmark, a live dashboard screenshot, and a configuration table that matches the actual environment variables in `src/weebarr/settings.py`.

## [0.1.10] - 2026-06-05

### Fixed

- Rebalanced the seasonal stat cards so each metric value sits in a consistent centered lane instead of drifting based on label length.
- Restored full width to the stat titles and supporting text while keeping the metric emphasis visually aligned across all four cards.
- Changed seasonal section grouping so `Score` now creates star-based rating bands and `Next airing` now creates day/date headers instead of reusing the popularity buckets.

## [0.1.9] - 2026-06-05

### Fixed

- Raised the seasonal dashboard dropdown layers above the stat cards and anime posters so open menus render on top instead of disappearing behind content panels.
- Normalized the season year input into a styled textfield with consistent width and no native spinner chrome so the year no longer clips across desktop and mobile layouts.
- Kept the top action row and filter controls in the same visual system across responsive breakpoints while preserving the inline mobile expansion flow.

## [0.1.8] - 2026-06-05

### Changed

- Replaced the seasonal dashboard's native browser selects with custom in-page dropdown components for the season picker, status filter, sort control, and seasonal quick filter.
- Reworked the seasonal filter/topbar control styling so the dashboard uses one consistent control language across desktop and mobile instead of mixing browser-default dropdown behavior with custom buttons.

### Fixed

- Upgraded mobile card expansion to open a full inline detail panel using the same information model as the desktop spotlight.
- Bound card selection directly to the rendered card surface buttons so mobile taps reliably expand and collapse the inline detail panel.

## [0.1.7] - 2026-06-05

### Fixed

- Preserved the new custom select chevrons by switching shared control backgrounds to `background-color`, which avoids wiping select background images out with a shorthand reset.

## [0.1.6] - 2026-06-05

### Fixed

- Reworked the wide-screen Seasonal filter layout so the `Hide Requested` row no longer spills into the spotlight column on larger desktop viewports.
- Added explicit dropdown chevrons and spacing to the app's select controls so filter and season pickers read like dropdowns instead of plain text boxes.
- Moved the quick `Filters` menu to open below its trigger instead of covering the stat cards above it.

## [0.1.5] - 2026-06-04

### Fixed

- Forced the Seasonal `has-hide-toggle` filter variant to collapse to a single column on smaller screens so the filter row no longer overflows horizontally on mobile widths.

## [0.1.4] - 2026-06-04

### Fixed

- Prevented the Seasonal filter row from overflowing into the spotlight panel at desktop widths by tightening the `Hide Requested` control footprint and adding a matching breakpoint override.

## [0.1.3] - 2026-06-04

### Added

- Seerr/TMDb artwork preference for matched anime cards and spotlight art, with AniList art kept as fallback.
- A `Hide Requested` switch on the Seasonal page for trimming fully requested or available titles from discovery browsing.

### Changed

- The Requests page now focuses on anime for the selected season that are already requested, partially requested, or fully available in Seerr instead of mirroring the generic seasonal feed.

## [0.1.2] - 2026-06-04

### Fixed

- Restored the main dashboard layout by fixing a broken CSS rule that stopped the browser from parsing large sections of the seasonal view styles.

## [0.1.1] - 2026-06-04

### Added

- Dedicated settings page for Seerr connections with persisted URL, API key, and request defaults.
- Connection test/save API endpoints and a real requests route instead of placeholder navigation.

### Changed

- Dashboard interactions now support working pagination, filters, theme persistence, and mobile-friendly detail expansion.
- Light mode glass, toast, and request UI styling now use bright variants instead of dark carryovers.
- Seasonal audio metadata lookup runs with higher concurrency to reduce slow cold loads.

## [0.1.0] - 2026-06-04

### Added

- Initial Weebarr FastAPI application.
- Seasonal anime discovery from AniList.
- Seerr search/status matching for requestable, requested, available, partially available, and missing-match states.
- One-click TV anime request forwarding to Seerr.
- Deep Zone-inspired dashboard UI with seasonal filters, popularity buckets, anime cards, and spotlight details.
- Docker and Docker Compose examples using the public GHCR image.
- GitHub Actions CI and GHCR publishing workflow.
