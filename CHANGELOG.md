# Changelog

All notable changes to Weebarr will be documented in this file.

## [0.1.79] - 2026-06-20

### Fixed

- Lowered the desktop Settings tab rail by 3 more pixels so the selected tab now sits flush with the main panel surface instead of leaving a visible seam, while the mobile detached layout stays unchanged.

## [0.1.78] - 2026-06-20

### Fixed

- Removed the inset top highlight from the attached desktop Settings panel shadow so the selected tab no longer has a stationary seam line pinned beneath it, while the mobile detached layout still keeps the original panel styling.

## [0.1.77] - 2026-06-20

### Fixed

- Removed the attached desktop Settings panel's top rule entirely so the selected tab no longer reads as separated from the main body, while the mobile detached tab layout remains unchanged.

## [0.1.76] - 2026-06-20

### Fixed

- Removed the remaining Settings tab gap by cutting the panel's top rule out from under the selected desktop tab, so the active tab now reads as a continuous piece with the main body while the mobile detached layout stays unchanged.

## [0.1.75] - 2026-06-20

### Fixed

- Restored the selected desktop Settings tab's connection to the main panel body by moving the tab rail and panel overlap together, so the active tab stays visually fused to the surface instead of floating above it.

## [0.1.74] - 2026-06-20

### Fixed

- Lowered the desktop Settings tab rail by 3 pixels while keeping the same-height inactive-behind and active-over-panel treatment, so the selected tab sits closer to the panel body without bringing back the detached seam.

## [0.1.73] - 2026-06-20

### Fixed

- Changed the Settings tab layering so inactive tabs stay tucked behind the panel while the selected tab alone rises above it, which removes the remaining detached-looking seam under the active Settings tab.

## [0.1.72] - 2026-06-20

### Fixed

- Reworked the Settings tab seam treatment so the active desktop tab now covers the panel rule directly instead of carving a widened cutout through the panel top, which restores a cleaner attached-tab look across every Settings section.

## [0.1.71] - 2026-06-20

### Fixed

- Restored the attached desktop Settings tab layout so the selected tab now tucks into the panel body again instead of dropping into the detached mobile-style state on wide screens.

## [0.1.70] - 2026-06-20

### Fixed

- Extended the selected Settings tab top-rule cutout farther into the neighboring tab shoulders so the panel seam no longer crowds the active tab's outer curves while the mobile detached layout still keeps the bridge disabled.

## [0.1.69] - 2026-06-20

### Fixed

- Replaced the Settings panel's continuous top border with segmented left and right top-rule spans so the selected tab no longer shows any seam underneath while inactive tabs still keep their edge definition.

## [0.1.68] - 2026-06-20

### Fixed

- Removed the remaining top seam under the selected Settings tab by masking the panel border only beneath the active attached tab, so the selected tab now visually shares the panel body while inactive tabs keep their own edge line.

## [0.1.67] - 2026-06-20

### Fixed

- Corrected the Docker/runtime version fallback so live health and setup surfaces now report the shipped app version accurately after deployment.

## [0.1.66] - 2026-06-20

### Fixed

- Unified the selected Settings tab surface with the main panel body so the active tab now reads as one continuous shell instead of a separate segmented cap.

## [0.1.65] - 2026-06-20

### Fixed

- Moved the Settings tab rail down and tucked it behind the main Settings panel so the body shell cleanly overlaps the tabs instead of leaving them floating in front.

## [0.1.64] - 2026-06-20

### Fixed

- Dropped the Settings tab rail by 3 pixels so the tabs sit lower against the panel body and read as a more continuous shell again.

## [0.1.63] - 2026-06-19

### Fixed

- Seasonal cards and spotlight panels now prefer backend-provided TMDB artwork first, with AniList art only as the fallback when no mapped poster or backdrop is available.

## [0.1.62] - 2026-06-19

### Fixed

- Unified seasonal poster and spotlight artwork rendering across Seerr and Sonarr Direct by preferring the shared AniList art fields in the dashboard UI, so backend swaps no longer change the visible art treatment.

## [0.1.61] - 2026-06-19

### Fixed

- Relaxed Sonarr Direct availability classification so monitored titles that are only missing one or two episodes now stay `Available` instead of being flagged as an issue, while larger gaps still fall back to `Partially Available`.
- Added breathing room around the seasonal stat-card row and shifted the cyan bloom origin slightly off-card so the active quick-filter glow no longer looks cut off on the left edge.

## [0.1.60] - 2026-06-19

### Added

- Added a new `Backends` docs page plus README and docs-site copy updates that explain the Seerr and Sonarr Direct setup paths in plain language.

### Fixed

- Turned the seasonal stat cards into real quick filters so `Anime This Season` resets the seasonal view, `Airing Soon` narrows to the next-seven-days slice, and other cards filter to their matching backend-aware states.
- Swapped the active seasonal stat-card highlight over to a color-aware outer glow and border treatment that matches each card instead of the old generic neon hover ring.
- Fixed Sonarr Direct library matching for full-library titles that only expose reliable overall episode statistics by fetching full series details for existing Sonarr matches before classifying availability.

## [0.1.59] - 2026-06-19

### Fixed

- Removed the extra post-account-created pause in first-run auth so setup now redirects straight into request-backend onboarding instead of stopping on an unnecessary intermediate state.
- Reworked Sonarr Direct onboarding and Settings into a split connection/defaults layout with `http` or `https`, host, and port fields plus a local `Validate Sonarr` action, and removed the duplicate neon ring from the selected backend choice cards.

## [0.1.57] - 2026-06-16

### Fixed

- Removed the extra neon hover ring from active Settings tabs, limited the tab hover outline to the top and side shell instead of the bottom edge, and fused the tab rail back into the Settings body without the stray seam line.
- Bumped `starlette` to `1.3.1` so the release clears the current `pip-audit` findings before shipping.

## [0.1.56] - 2026-06-15

### Fixed

- Bumped `python-multipart` to `0.0.31` so the release clears the new 2026 `pip-audit` multipart advisories again.

## [0.1.55] - 2026-06-15

### Fixed

- Reworked first-run backend onboarding into a real post-auth branch so setup now starts with a backend chooser, then opens the matching Seerr or Sonarr Direct form, and also allows `Skip Setup` for finishing backend config later in Settings.
- Restored the attached Settings tab shell so the active tab highlight reaches the panel border again without leaving a stray divider line between the tab rail and the body.

## [0.1.54] - 2026-06-15

### Added

- Added an optional `Sonarr Direct` request backend alongside the existing Seerr flow, including backend-aware setup, settings, request dispatch, automation routing, and request history metadata.
- Added a dedicated `/setup/backend` onboarding step so first-run setup now finishes by choosing and configuring the active request backend.
- Added a Sonarr-specific request modal with season selection, monitor mode, search-on-add, and season-folder controls for direct Sonarr adds and updates.

## [0.1.53] - 2026-06-15

### Fixed

- Limited the character voice-cast disclosure neon highlight to hover while the wrapper is closed so click focus and expanded state no longer leave the box glowing.

## [0.1.52] - 2026-06-15

### Fixed

- Expanded the opened character voice-cast neon highlight to the full disclosure box instead of only outlining the toggle row.

## [0.1.51] - 2026-06-15

### Fixed

- Unified the seasonal header pill fill so the season segment, year block, and adjacent arrow buttons all share the same glass background instead of the season side rendering darker than the rest.

## [0.1.50] - 2026-06-15

### Fixed

- Increased the seasonal header control fill opacity so the season picker and adjacent navigation blocks read as solid glass again on desktop and mobile.
- Kept the masked episode glyph and shorter `X Episodes` stat treatment aligned cleanly in the seasonal card detail row.
- Replaced deprecated FastAPI startup and shutdown event hooks with a lifespan handler and updated GitHub Actions workflows to Node 24-compatible action releases.

## [0.1.49] - 2026-06-15

### Fixed

- Restored the filled glass background on the seasonal header season selector while keeping the label centered cleanly inside the pill.
- Reworked the seasonal episode stat into a shorter icon-led `X Episodes` treatment using the new masked episode glyph, with centered vertical alignment on desktop and mobile.

## [0.1.48] - 2026-06-14

### Fixed

- Recentered the seasonal header season label both vertically and horizontally without clipping the text or disturbing the shared dropdown chevron styling.
- Swapped the character voice-cast disclosure control over to the shared masked dropdown arrow so the icon inherits the neon accent color and sits cleanly beside the cast summary on desktop and mobile.

## [0.1.47] - 2026-06-14

### Fixed

- Tinted the seasonal popularity icon with the same accent color as its stat text so the glyph no longer renders as a flat dark bitmap.
- Centered the seasonal picker label vertically so the selected season text sits evenly within the top control pill.

## [0.1.46] - 2026-06-14

### Fixed

- Removed the extra cyan hover glow from already-selected seasonal anime cards so the active state keeps its intended single pink treatment.
- Added total episode counts beside the score and popularity metadata on seasonal cards and expanded detail views.
- Changed character voice-cast sections into per-character disclosures so large casts stay easier to scan on both desktop and mobile.

## [0.1.45] - 2026-06-12

### Fixed

- Restored the seasonal header season dropdown by removing the clipping that hid the open menu.
- Extended the seasonal selector hover/open outline cleanly across the left segment and suppressed the divider line while active so the highlight no longer collapses into the year separator.

## [0.1.44] - 2026-06-12

### Fixed

- Raised the seasonal selector highlight layer above the pill background so the active left-segment outline renders cleanly instead of collapsing into the divider accent.

## [0.1.43] - 2026-06-12

### Fixed

- Moved the seasonal header selector highlight to the full left segment so the active hover/open ring lines up with the outer pill instead of drawing inset.

## [0.1.42] - 2026-06-11

### Fixed

- Extended the seasonal header selector styling so the season highlight spans the full left segment instead of floating inset inside the pill.
- Bound the small-card `Request in Seerr` action directly on each card button so it no longer gets lost behind the card selection handlers.

## [0.1.41] - 2026-06-11

### Fixed

- Moved the voice-actor AniList action left so the card no longer leaves an awkward empty gutter under the avatar column.
- Removed the shared cyan-pink hover edge from already-active pink navigation states so the selected Seasonal rail keeps its intended single red treatment.

## [0.1.40] - 2026-06-11

### Fixed

- Widened the voice-cast layout so the `Voice Cast` label and actor cards use the full character rail instead of leaving a dead media gutter beside the card body.
- Tightened the shared hover chrome so gradient outlines replace the resting border cleanly on buttons, selects, and other outlined controls instead of doubling up.
- Reshaped the sidebar theme mode rows to highlight the full row shell and attached the settings tabs to the panel body so the tab rail no longer looks overlaid on top of the page.

## [0.1.39] - 2026-06-08

### Changed

- Added a dedicated light-theme Weebarr wordmark so the logo text switches to black in light mode while preserving the colored `W` mark.
- Refreshed the README and GitHub Pages docs with the new dark, light, login, requests, and settings screenshots.

## [0.1.38] - 2026-06-08

### Fixed

- Fixed seasonal anime card selection so clicking a normal card surface reliably opens and switches the spotlight again instead of being ignored by the card click guard.

## [0.1.37] - 2026-06-08

### Added

- Added a dedicated `API` settings tab for the automation API key, including one-click generation or regeneration and a one-time reveal of the new key value.
- Added a GitHub Pages deployment workflow that publishes only the repo `docs/` folder as the public documentation site.
- Added a public theme-template documentation page and a downloadable `docs/theme-reference.json` manifest for community theme authors.

### Changed

- Promoted the new markdown documentation set into the repo `docs/` folder and updated the README to point at the Pages-backed docs instead of the old repo wiki.
- Changed the default documented host port from `8080` to `18080` across compose examples, local testing docs, and deployment guides while keeping the container listen port at `8888`.
- Updated the settings model documentation to reflect the new `API` tab and the automation cadence `days + hours` format.

## [0.1.36] - 2026-06-06

### Fixed

- Reverted the `0.1.35` forced-sidebar request behavior so small seasonal-card request clicks no longer hijack the spotlight state.
- Kept the click-routing fix that lets the small-card `Request in Seerr` button bypass the card-select handler and send the same real request as the expanded spotlight action.

### Documentation

- Added a repo wiki covering features, settings, API behavior, troubleshooting, Docker Desktop deployment on Windows and Linux, and other deployment options.

## [0.1.35] - 2026-06-06

### Fixed

- Stopped seasonal card request clicks from being intercepted by the card-surface select handler, so `Request in Seerr` now sends the request directly from the small card while also focusing the same title in the detail sidebar.

## [0.1.34] - 2026-06-06

### Fixed

- Finished the Seerr anime-default follow-up by initializing the no-override request path correctly and aligning the request-path assertions with the final error copy so CI stays green.

## [0.1.33] - 2026-06-06

### Fixed

- Corrected the anime request path so Weebarr no longer tries to send Seerr's internal default Sonarr config ID `0` back as a request override when `Force Series Type` is enabled.
- Changed Weebarr to carry Seerr's saved anime profile, anime root folder, anime language profile, and anime tag defaults through anime requests unless you explicitly override them in Settings.
- Stopped treating a missing `animeSeriesType` field from Seerr as `Anime / Absolute`, and now surface a clearer message when Seerr does not expose that metadata.
- Updated the Connections help copy and test output so `Series Type` reflects what Seerr actually exposes instead of implying a false default.

## [0.1.32] - 2026-06-06

### Fixed

- Replaced the clipped sidebar pseudo-tooltips with a shared floating tooltip layer so the auth and Seerr status help now render above the page shell instead of being cut off at the sidebar edge.
- Hardened the seasonal and requests mobile breakpoints so the content rail stays single-column and no sidebar chrome bleeds into smaller layouts.
- Tightened the built-in `Monochrome` palette to a true grayscale accent family and removed the remaining red/pink selected-state treatment from spotlight and rank surfaces.

## [0.1.31] - 2026-06-06

### Fixed

- Softened the seasonal stat-card copy layout, widened the centered season selector clearance, and added more bottom scroll buffer so the desktop seasonal page reads cleanly end-to-end again.
- Removed the dead three-dot affordance from anime cards and tightened the spotlight pill spacing so the poster/title transition feels intentional instead of cramped.
- Converted the settings sidebar auth and Seerr cards into one-line connected states with runtime tooltip details, and raised the tooltip layer so overlays no longer render behind the main page content.
- Leveled the `Connections` form rows and simplified the toggle sections so `Strict Monitoring` and `Quality Profile` align with the rest of the settings grid.
- Fixed theme token propagation so `Monochrome` drops the leftover accent chrome and `Color Picker` updates borders, highlights, and other visible UI surfaces instead of only recoloring icons.

## [0.1.30] - 2026-06-06

### Fixed

- Restored the desktop seasonal shell to a stable two-column layout so the left content rail owns the header, stats, filters, buckets, and pagination while the spotlight stays pinned on the right without crowding the list.
- Tightened the seasonal header controls and spotlight spacing, including the centered season selector, aligned Refresh/Scan buttons, and a cleaner gap between the spotlight poster and the rank/audio pill row.
- Reworked Settings into attached tabs with compact, top-aligned panels so the `Weebarr`, `Automation`, `Authentication`, and `Connections` sections no longer feel detached or vertically stretched.
- Replaced the native-looking theme zip upload field with a styled Weebarr upload control and added the shared upload asset to both the docs bundle and the live static image set.
- Split automation cadence into persisted `days + hours` inputs, kept backward compatibility for older day-only configs, and added validation so `0d 0h` is rejected.
- Reduced the size of settings summary/status cards, aligned the connection dashboards more tightly, and added themed hover tooltips to the sidebar status text and live endpoint/session text.

## [0.1.29] - 2026-06-05

### Security

- Upgraded `python-multipart` to `0.0.27` so the repo clears the current `pip-audit` vulnerability checks again after the automation/theme release work.

## [0.1.28] - 2026-06-05

### Added

- Added a full theme engine with built-in `Neon Lights`, `Monochrome`, and editable `Color Picker` palettes, plus safe theme import from JSON URLs or `.zip` theme packs and a shipped reference manifest for community themes.
- Added an `Automation` settings section and server-side seasonal auto-request engine with bucket selection, manual `Scan now`, configurable scan cadence, and persisted scan history for `S-Tier`, `Canon`, `Bingeable`, and `Filler`.

### Changed

- Rebuilt Settings into named top tabs for `Weebarr`, `Automation`, `Authentication`, and `Connections`, keeping one section visible at a time while supporting hash deep links like `#automation` and `#connections`.
- Extended the Weebarr settings payload to persist theme selection, editable theme tokens, and automation preferences alongside the existing catalog behavior controls.
- Added a real seasonal-page `Scan` action and switched the `Refresh` and `Scan` buttons over to the repo icon assets.

### Fixed

- Centered the seasonal season-selector text independently from the right-aligned chevron and reworked the `Filters` trigger so its label and chevron stay visually centered together.
- Restored the desktop main-column scroll behavior so the seasonal header, stats, filters, buckets, and pager move together while the sidebar keeps its own independent scroll track.
- Moved the spotlight and inline detail pill row lower so the rank and audio badges sit more comfortably between the poster and the title block instead of touching the artwork edge.
- Cleared the new automation/theme mypy regressions so the repo is back to a clean CI state with passing type checks.

## [0.1.27] - 2026-06-05

### Fixed

- Updated the seasonal and settings shells to use the repo icon assets for sidebar navigation, stat cards, theme mode controls, and dropdown carets instead of the previous mixed SVG/text icon set.
- Changed the desktop spotlight close button to return the sidebar to its empty `Select an anime` state while keeping the mobile inline close button as a full collapse of the expanded card.
- Moved the spotlight rank and audio pills beneath the artwork, removed outward-arrow glyphs from AniList/trailer/cast links, and added hover explanations for core metadata like rating, popularity, and availability.
- Tightened the seasonal top stat-card proportions so the cards stay flatter and more consistent with the sidebar width, with the new asset-driven `Airing Soon` icon centered correctly.
- Stopped the `CI Pipeline` from failing on every release by aligning mypy with normal optional checking and making the Bandit gate fail only on medium-or-higher findings instead of low-severity subprocess noise.

## [0.1.26] - 2026-06-05

### Fixed

- Decoupled the desktop seasonal and requests content scroll from the sidebar so the bucket list and pager now use their own scroll region instead of stretching the full page shell.
- Restored normal document scrolling on smaller breakpoints so mobile and tablet layouts do not inherit the desktop overflow lock.

## [0.1.25] - 2026-06-05

### Added

- AniList character and voice actor details now load on demand for the selected anime and render at the end of the desktop spotlight and inline mobile detail views.

### Changed

- Kept the seasonal feed responsive by fetching cast data only for the currently expanded title instead of inflating the base seasonal payload for every card.

## [0.1.24] - 2026-06-05

### Fixed

- Stopped sending Seerr request-time Sonarr/profile/root defaults automatically, so Weebarr can now defer to Seerr's own anime request defaults unless you explicitly force an override.
- Added `Force Series Type` and `Force Quality Profile` controls to Settings, including real clearing behavior for saved Sonarr/profile/tag overrides instead of trapping older values in the config.
- Prevented the Seerr connection test from auto-filling detected Sonarr defaults back into the form, which had been making accidental permanent overrides too easy.

## [0.1.23] - 2026-06-05

### Security

- Removed the production-usable static session-secret fallback and replaced it with fail-closed startup checks for configured auth, plus ephemeral setup-only signing when the instance is still unclaimed.
- Hardened first-run setup so Weebarr no longer trusts client-controlled `Host` or forwarded-IP headers to decide whether setup is local, and added an optional `WEEBARR_BOOTSTRAP_TOKEN` path for intentional remote first-run claims.
- Stopped deriving Plex callback origins from request host values and now require `WEEBARR_PUBLIC_URL` for Plex-auth/public deployments.
- Restricted the automation API key to safe read/request routes so it can no longer mutate admin authentication state or Settings.
- Added lightweight in-app rate limits for local login, first-run setup, and Plex-auth starts.

### Infrastructure

- Pinned the runtime dependency set to known-safe versions, including safe Starlette and `python-dotenv` releases.
- Replaced the old `safety` CI dependency check with `pip-audit`, and added `SECURITY.md`, Dependabot, and CodeQL workflow coverage.

### Docs

- Added `.env.example` and updated the README and compose examples to document `WEEBARR_PUBLIC_URL`, optional bootstrap-token setup, and reverse-proxy expectations for public deployments.

### UI

- Moved the seasonal card rank and audio chips into a shared pill row beneath the poster, with the rank badge now using the same pill shape language as the dub tag.
- Changed the non-dub fallback label from origin-specific text to `EN Sub`.
- Flattened the seasonal-only stat cards further and nudged the `Airing Soon` icon geometry so the top summary row fits the intended elongated layout more cleanly.

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
