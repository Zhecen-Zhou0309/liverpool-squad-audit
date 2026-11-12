# Methodology and Phase One roadmap

## Objective

Combine matches, appearances, player roles and availability over a consistent period to identify roles that warrant recruitment review, the capabilities they lack, and the supporting evidence and alternative explanations. Phase Two will use those capability profiles to assess prospects and established players.

The current version implements input validation, team-performance analysis and role-minute concentration. Verified availability, backup capability, event locations and tactical fit are not yet integrated, so it cannot complete a position-level recruitment assessment.

## Scope

- Team: Liverpool men's first team.
- Season: 2026–27.
- Default cutoff: November 11, 2026, including completed matches on that date.
- Competition: Premier League only; cup and European performances are not pooled into the same benchmark.
- Output: descriptive statistics, review signals and evidence coverage, without uncalibrated recruitment scores or confidence probabilities.

## Current evidence chain

1. Verify that matches are completed, in scope and from the correct competition.
2. Compare chance creation and prevention with other teams over the same period.
3. Inspect sensitivity to recent-match windows, venue and red-card exclusions.
4. Check appearance completeness and concentration in actual match roles.
5. Keep an assessment at **Insufficient evidence** when the required information is unavailable.

## Work needed to support recruitment recommendations

### A. Squad coverage

Collect starting lineups, substitutions and role minutes, and verify the first-team and available-backup roster at the cutoff. Not appearing may reflect selection rather than inability. Registered positions alone are insufficient.

Assess backup assignments using a separate roster and role-capability evidence. One versatile player cannot cover two simultaneous vacancies in the same scenario.

### B. Availability and workload

Distinguish injuries, suspension, rest and non-selection, with effective dates and traceable sources. Do not infer injury from absence. Include European and cup workloads when assessing load, while keeping performance comparisons stratified by competition or difficulty.

### C. Capability and tactical responsibility

Event data can support assessment of progression, box receiving, chance creation, aerial work and transition defending. Choose metrics for the actual role. Defensive event counts depend on possession and opportunity; more tackles do not automatically mean better defending.

Where event locations or sequences are unavailable, use traceable video annotations. Record the phase, score state, opposition structure, involved players and clip timestamp. Full-match xGA cannot distinguish low-block, transition and set-piece problems by itself.

### D. Decisions

Only propose recruitment when repeated match problems are supported by role and squad evidence and tactical or availability explanations have been examined. A recommendation should state:

- The position and role, such as a midfielder who can progress possession under pressure and provide recovery coverage.
- The gap type: starting-quality upgrade, rotation depth, complementary role or succession planning.
- Supporting evidence, sample range and unresolved explanations.
- Review or recruitment priority; numeric scoring requires separate sensitivity analysis and historical validation.

## Validation design

Program tests cover perspective reversal, missing values, cutoffs, unknown red-card status, recent-window ordering, sample thresholds, duplicates, invalid numbers, overlapping role minutes, partial lineups and complete appearance records. Reproduction tests verify exact inputs and outputs and deliberate mismatch failures.

Football judgments still require historical evaluation and human review. Do not use subsequent transfers to construct an earlier answer. Freeze information to what was available at the assessment date to avoid leakage.
