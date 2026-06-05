# Changelog

All notable changes to Weebarr will be documented in this file.

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
