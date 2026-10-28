# Verification

Baseline: `bb165fa1721a795e74ff4055edc7f93b4659582c`

Executed in the preparation environment:

- `node --check PulseFit/dist/app.js`: passed.
- `node --check PulseFit/dist/sw.js`: passed.
- Playwright 1.64.1, bundled Chromium, mobile viewport 390 × 844: **10 tests passed**.
- Offline reload, export/import round trip, invalid backup rejection, corrupt storage protection, legacy history, legacy catalog repair, storage quota failure, exercise replacement identity and persistent timer tested.
- A real iPhone was **not** tested.
- WebKit could not launch locally because required Linux libraries are missing. No WebKit pass is claimed. CI installs those dependencies and is configured to run the suite in Chromium and WebKit; CI itself has not been run on GitHub.
- No GitHub push, Pull Request, merge, Pages configuration change or deployment performed.

See `tests/test_app.py` for exact assertions. The successful local run output:

```text
Ran 10 tests in 12.435s
OK
```

Images are existing repository assets, not a newly sourced or license-verified dataset. See README.md for limitations and iPhone acceptance checks.

## Workout deletion update

- Confirmed deletion for all history entries, including legacy entries without IDs.
- Statistics and exercise history recalculate; failed storage writes roll back deletion.
- Service worker cache bumped to v5.
- Chromium mobile viewport: 14 tests passed, including 4 deletion tests.
- iPhone and WebKit not reverified. No push or deployment performed.
