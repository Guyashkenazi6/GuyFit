# Interactive weekly planner — 2026-10-30

## Executed checks

- `node --check` passed for app.js, planner.js and sw.js; `git diff --check` passed.
- `uv run python -m unittest discover -s tests -v`: **29 tests passed** in 34.315 seconds using Playwright bundled Chromium (22 regression + 7 new planner tests).
- New coverage: custom pairs, cancellation, single groups without duplicate exercises, day counts, completion persistence without fabricated history, active-session guard, mobile overflow, Escape/focus restoration, set changes/reload, completed-log preservation, confirmation cancellation, and storage-failure rollback.
- Mobile (390×844) and desktop visual inspection performed with synthetic local data. No existing user data was imported or changed.

## Limitations and release

- Local WebKit execution unavailable: browser download completed but required Linux shared libraries are missing. WebKit remains required in GitHub CI; Chromium results are not Safari certification.
- System Chromium initially completed assertions but hung on test-browser teardown; the completed 29-test run above uses the matching Playwright browser and exits normally.
- Service-worker cache is now v8, includes planner.js and personal.css, and retains the existing wait-for-closed-tabs update behavior.
- No production deployment performed as part of local verification. Export a backup before updating; finish active workouts and close all old tabs/PWA windows before reopening online.
