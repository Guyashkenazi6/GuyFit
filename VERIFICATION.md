# Verification: leg exercises and CI/CD

Date: 2026-10-28. Patch base: `2f9950e2af2f49774f48e918f242bbc629ef9ed4` (origin/main, merged workout experience update).

## Implemented

- Stable exercise IDs 49–55; original IDs 1–48, storage key and backup version unchanged.
- Hebrew legs category across library, replacement picker, workout view and statistics.
- Seven original paired-position SVG illustrations stored under assets/legs; no external asset requests.
- Hebrew muscles, execution, breathing, common mistakes and easier alternatives.
- New programs include a fourth, five-exercise legs day. Existing three-day programs remain untouched. Explicit append button, duplicate prevention, active-session guard and failed-save rollback.
- Service worker cache v6 includes legs.js and all seven illustrations; no skipWaiting, forced refresh or LocalStorage clearing.
- Existing browser CI retained. Pages runs automatically on main push, or manually; deployment needs successful Chromium AND WebKit tests for that workflow's commit. Feature-branch runs cannot deploy.
- Pages output layout and root redirect unchanged. Deployment job has contents:read, pages:write and id-token:write; test jobs have contents:read only.

## Actual local checks

Commands used:

```sh
node --check PulseFit/dist/legs.js
node --check PulseFit/dist/app.js
node --check PulseFit/dist/sw.js
git diff --check
/home/rakazo/.local/share/uv/tools/playwright/bin/python -m unittest discover -s tests -v
BROWSER=webkit /home/rakazo/.local/share/uv/tools/playwright/bin/python -m unittest discover -s tests -v
```

- All three JavaScript syntax checks passed.
- Diff whitespace check passed.
- Playwright 1.64.1 bundled Chromium, mobile 390×844: **21 tests passed in 24.229 seconds**.
- Existing 14 tests retained; seven additional cases cover catalog/filters/guidance/decoded SVGs, adding legs without replacing an existing plan, failed-save rollback, workout/backup/history persistence, replacement, legacy three-day persistence, exact /GuyFit/PulseFit/dist/ service-worker scope and offline access to all seven SVGs.
- Mobile library and exercise detail screenshots generated and visually inspected. Original vector diagrams are schematic, not anatomical photographs or professional form instruction.
- **WebKit did not launch: required Linux shared libraries are missing. Zero WebKit tests ran locally; no WebKit pass is claimed.** GitHub workflows install browser system dependencies with --with-deps and block deployment if this browser fails.

## Not verified / still required

- Real iPhone/Safari/PWA interaction and service-worker upgrade from an already installed user session.
- Actual GitHub Actions checks, Pages environment approval/settings and live deployment.
- Manual check of exercise suitability and load selection for the user's needs.

No commit, push, PR, merge, account settings change, external messaging or deployment was performed. Work was done in a separate local worktree based on the merged main branch; earlier local changes were left untouched.

## Machine exercise addition, 2026-10-28

- Added IDs 56 (leg extension) and 57 (seated leg curl), original local paired-position SVGs, Hebrew setup and safety guidance. Seated curl requires a compatible model, which cannot be confirmed from the photograph alone.
- Existing default and saved programs remain unchanged; choose either exercise via the existing replacement picker. No storage format changes.
- Cache v7 precaches all nine leg illustrations.
- Actual checks: node --check on legs.js, app.js and sw.js passed; git diff --check passed; full Chromium suite: 22 tests passed. Includes saving/reloading both machine exercises, catalog/image validation and all nine assets offline under the Pages subpath.
- WebKit attempted but could not start due to missing system libraries; zero WebKit tests ran locally. GitHub still requires both browsers before Pages deployment.
- Manual check required: confirm machine modes and fit with a gym instructor; inspect illustrations and setup on your phone.

## User Mac verification, 2026-10-29

- JavaScript syntax checks passed for legs.js, app.js and sw.js.
- Chromium: 22 tests passed in 31.566 seconds.
- WebKit: 22 tests passed in 40.861 seconds.
- Real iPhone/PWA upgrade and GitHub Actions/Pages deployment remain unverified.
