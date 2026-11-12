# Changelog

## v0.1.1 — 2026-11-11

- Translate the dashboard, role labels, reports, validation errors, CLI messages and documentation into English.
- Preserve the existing commit history and the `v0.1.0` baseline.
- Refresh output hashes for the English reports while retaining the same raw input and numeric analysis.
- Regenerate source and history archives and English report artifacts.

## v0.1.0 — 2026-11-11

- Import match statistics, explainable rules, player-role minute checks, report exports and the local dashboard.
- Pin the reference Python interpreter and transitive dependencies; add Makefile entry points.
- Verify frozen input/output SHA-256 hashes and record code and environment provenance for each run.
- Add 15 offline tests covering analysis and reproduction failures.
- Pin CI action revisions and configure dependency and dashboard-startup checks. Remote execution must be verified after the first upload.
- Analyze Premier League data through November 11, 2026. Withhold definitive recruitment-position conclusions when player-role, appearance and availability evidence is missing.
