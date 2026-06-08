---
title: Theme Template
---

# Theme Template

This page gives you a reference shape for building a community Weebarr theme.

Weebarr themes are validated JSON token packs. They are not raw CSS, JavaScript, or asset bundles.

## How Imports Work

Weebarr accepts theme imports from:

- a direct URL to a `theme.json` file
- a `.zip` archive that contains `theme.json`

If you are sharing a theme with other people, a direct GitHub raw URL or a small zip with a single `theme.json` file is the safest format.

## Required Structure

A theme manifest should contain:

- `id`
- `name`
- `description`
- `author`
- `tokens.dark`
- `tokens.light`

## Reference Manifest

You can use this live file as a starting point:

- [theme-reference.json](theme-reference.json)

## Sample Theme JSON

```json
{
  "id": "community-theme-reference",
  "name": "Community Theme Reference",
  "description": "Reference token pack for building custom Weebarr themes.",
  "author": "Weebarr",
  "tokens": {
    "dark": {
      "bg": "#050911",
      "bg2": "#08111b",
      "pageTail": "#03060b",
      "pageGlowA": "#28c7ff21",
      "pageGlowB": "#ff3c7d1f",
      "pageGlowC": "#502aff14",
      "panel": "#101720db",
      "panel2": "#141c27b8",
      "panel3": "#0d121ae6",
      "mediaScrim": "#05091194",
      "line": "#7a97b333",
      "lineStrong": "#7ebfe161",
      "text": "#f5f7fb",
      "muted": "#99a8bb",
      "subtle": "#6f7e90",
      "cyan": "#28c7ff",
      "pink": "#ff3c7d",
      "purple": "#b466ff",
      "green": "#55e18d",
      "warning": "#ffd166"
    },
    "light": {
      "bg": "#edf6ff",
      "bg2": "#f8fbff",
      "pageTail": "#e9f4ff",
      "pageGlowA": "#28c7ff33",
      "pageGlowB": "#ff3c7d29",
      "pageGlowC": "#502aff14",
      "panel": "#ffffffd1",
      "panel2": "#ffffffb3",
      "panel3": "#ffffffe8",
      "mediaScrim": "#edf6ffbd",
      "line": "#425d7c33",
      "lineStrong": "#28a1da6b",
      "text": "#121c2b",
      "muted": "#5d6e82",
      "subtle": "#778699",
      "cyan": "#28c7ff",
      "pink": "#ff3c7d",
      "purple": "#b466ff",
      "green": "#55e18d",
      "warning": "#ffd166"
    }
  }
}
```

## Token Notes

The important theme token groups are:

- `bg`, `bg2`, `pageTail`: page background layers
- `pageGlowA`, `pageGlowB`, `pageGlowC`: radial page glow colors
- `panel`, `panel2`, `panel3`: panel surfaces
- `mediaScrim`: overlay/scrim surfaces
- `line`, `lineStrong`: borders and dividers
- `text`, `muted`, `subtle`: typography levels
- `cyan`, `pink`, `purple`, `green`, `warning`: accent colors

## Good Theme Authoring Tips

- Keep enough contrast between `text` and `panel`
- Keep `line` subtle and `lineStrong` more visible
- Treat accent colors as functional, not only decorative
- Test both dark and light modes
- If you want grayscale, change the actual accent tokens too, not just icon colors

## Sharing Themes

The safest sharing options are:

1. commit `theme.json` into a repo and share the raw URL
2. zip only the `theme.json` file and share that archive

Do not ask users to paste CSS or JavaScript into Weebarr. Theme imports are intentionally token-only.
