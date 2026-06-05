# Changelog

All notable changes to Weebarr will be documented in this file.

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
