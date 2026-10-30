# Apple-inspired GuyFit refresh

## Direction and scope
A Hebrew, RTL, mobile-first web PWA, not an iOS native replica. The central job is to plan a week and reach a workout with a calm, legible hierarchy. Grouped neutral surfaces, a single blue action accent, green completion feedback and original line SVGs replace decorative gradients and emoji navigation. No new dependencies, remote fonts, telemetry, storage schema changes or workout migrations.

Applied the user-requested dickwu/apple-design-skill recipe (read 2026-10-30) and relevant reference excerpts: accessibility, layout, typography, color, buttons, tab-bars, dark-mode, materials, cross-platform and code-audit. Web foundations apply; native-only conventions and claims of native Liquid Glass do not. Translucency is limited to navigation/timer chrome with solid fallbacks.

## Changes
- `apple.css`: semantic light/dark palettes, system typography, responsive grouped cards, consistent inputs and buttons, safe-area-aware navigation, high-contrast/reduced-transparency/reduced-motion support.
- `index.html`: GuyFit branding, calmer copy, original accessible SVG navigation, labelled search and close controls, appearance-aware browser theme colors.
- `app.js`: current navigation exposed with `aria-current`; chart palette follows CSS and OS appearance changes.
- `manifest.webmanifest`: matching name and light startup background.
- `sw.js`: cache v9 includes design CSS; existing wait-for-old-tabs behavior retained. No localStorage data is removed.
- Tests avoid hardcoding the previous service worker cache version.

## Verification
- Chromium: 33 browser tests passed locally, including existing workout/planner regressions and four new design tests.
- Design tests cover 320/390/768/1280px widths, 125% root text, 44px navigation targets, light/dark palette contrast >=4.5:1 against surfaces, navigation semantics, active-workout persistence across appearance changes/reload, offline CSS.
- `node --check` passed for app.js, planner.js and sw.js; `git diff --check` passed.
- Mobile light/dark and workout screenshots visually reviewed. Synthetic data only.
- Local WebKit launch unavailable because OS shared libraries are missing; GitHub CI installs browser dependencies and runs both Chromium and WebKit before merge/deploy. CI status is the source of truth for those runs.

## Update safety
Finish an active workout, close all existing app/browser tabs, then reopen online if the old version remains. Do not clear site data. Local browser storage is not a backup; JSON export remains available in metrics.

## Limits
No physical iPhone, VoiceOver session or native Dynamic Type verification was performed. Palette contrast tests are not an exhaustive contrast audit of every illustration. Existing atlas artwork and app icons are unchanged.
