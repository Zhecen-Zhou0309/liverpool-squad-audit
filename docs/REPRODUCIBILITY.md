# Reproducibility

Git commits make code changes traceable. Reproducing a football analysis also requires fixed inputs, parameters and a recorded environment.

## What this version records

| Layer | Record |
|---|---|
| Code | Functional commits and the English release tag `v0.1.1` |
| Environment | `.python-version`, resolved package versions in `requirements.lock`, and reference system information |
| Data | Source URL, retrieval time and original CSV SHA-256 in `reproducibility/baseline.json` |
| Parameters | Liverpool, Premier League, 2026–27, cutoff 2026-11-11, season to date, red-card matches included |
| Results | SHA-256 hashes of the Markdown, JSON and match-ID outputs |
| Each run | Code commit, worktree status, actual Python/system, dependency-lock hash, and input/output hashes in `run_metadata.json` |

The initial import commits were created during project preparation and represent functional groups, not development on different past dates. Environment locking, data verification, CI and documentation were subsequent improvements. The English release adds a translation commit without rewriting that history.

## Rebuild the baseline

1. Select the release in a repository containing its history:

```bash
git switch --detach v0.1.1
```

2. Use Python 3.12.6. To run the dashboard, install the locked dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
```

The analysis core and reproduction checks need no third-party packages.

3. Restore the frozen input, or attempt a verified upstream download:

```bash
python scripts/fetch_data.py --manifest reproducibility/baseline.json
```

4. Run tests and rebuild the reports:

```bash
python -m unittest discover -s tests -v
python scripts/reproduce.py
```

A successful run prints `Reproduction passed` and writes reports under `reports/reproduced/`. It does not update the baseline automatically.

## Preserve the input

The upstream CSV changes as the season progresses or historical records are corrected. A SHA-256 hash identifies a file but cannot recover a missing file. Raw third-party data is not committed here, so cloning the source alone cannot guarantee future access to the original bytes.

Keep `data/local/E0-2627.csv` and `provenance.json`. The separate delivery artifact `liverpool-analysis-input-2026-11-11.zip` contains those files under `data/local/` and can be extracted into the project root. It is separate from the public source and is not automatically pushed to GitHub.

For other researchers to reproduce the real-match analysis, provide a persistent, accessible archive of the same input under the source's applicable usage terms. The code and synthetic tests can be reconstructed directly from Git; the real-match report additionally requires its exact input.

## Update data or methods deliberately

- Create a new commit and analysis date, retaining old tags and inputs.
- Review source changes before regenerating results; do not change a hash merely to make verification pass.
- Record both new input and output hashes and explain the change in the changelog.
- Do not use current availability information for past assessments.

## English release baseline

Version `v0.1.1` translates the interface, messages, documentation and reports. The raw input and numeric analysis are unchanged. Output hashes are updated because role names, explanatory text and report formatting are now English. The `v0.1.0` tag retains its original baseline and history.

## Limits

The dependency lock pins package versions, not wheel hashes, wheel files, system libraries or a container image. It does not guarantee operating-system or binary-level identity. The Python patch version is recorded; cross-platform behavior must be verified separately. Local input/output identity has been checked. GitHub CI runs only after publication and has not been assumed to pass remotely.
