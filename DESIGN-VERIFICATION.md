# GuyFit identity restoration — 2026-10-30

## Direction
The user rejected the white/blue redesign. Restore the previous graphite surfaces, soft blue display text, lime primary actions and original Hebrew hero copy. Keep the GuyFit name and consistent SVG navigation icons. This is intentionally a dark fitness interface, not a system-appearance clone.

Apple-design skill used selectively: read SKILL.md and relevant accessibility, layout, typography, color, designing-for-ios, buttons, motion, tab-bars and cross-platform references. Applied web-appropriate principles: readable hierarchy, keyboard focus, comfortable targets, meaningful feedback, reduced motion, and blur limited to functional chrome. No native-component claims or new dependencies.

## Changes
- Replaced the broad light/dark `apple.css` skin with a smaller craft layer over the existing `personal.css` design.
- Restored graphite/lime theme and PWA chrome regardless of OS appearance.
- Added a contextual next-incomplete-workout shortcut. An active session becomes a resume action without resetting logs. All-complete weeks hide it; undoing completion restores it.
- Refined disclosure, hover and set-completion feedback; no perpetual decorative animation.
- Preserved keyboard navigation, labeled SVGs, safe areas, larger text, high contrast and reduced-transparency support. Reduced motion also disables canvas confetti and scripted smooth scrolling.
- Service worker cache v10. Existing waiting lifecycle retained: updates do not replace a running session. No storage schema or migration changes.

## Verification
- Bundled Chromium: 36 browser tests passed locally. Covers existing data and workout/planner regressions, offline assets, 320/390/768/1280px layouts, 125% text, contrast, keyboard disclosure and new next/resume interactions.
- Syntax checks: app.js, planner.js, sw.js; git diff --check.
- Local WebKit cannot launch because system libraries are unavailable; GitHub CI installs them and runs the full Chromium/WebKit matrix before deployment.
- Mobile screenshots inspected locally for planner and builder.

## Update guidance
Finish an active workout, close all GuyFit tabs and the installed app, then reopen online. If the old version appears, close/reopen once more after the update downloads. Do not clear site data: workouts are stored locally.
