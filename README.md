# Liverpool Squad Audit

An explainable football squad analysis project using Liverpool FC as a case study.

**Phase One: analyze Premier League matches from the 2026–27 season through November 11, 2026, examine role coverage, and build evidence for recruitment decisions.**

This is an initial analysis tool. It does not yet provide a complete, evidence-backed verdict on which positions Liverpool should recruit.

## Features

- Download real Premier League match data; validate fields, dates and duplicate matches; record the source, retrieval time and SHA-256.
- Normalize home and away perspectives and calculate goals, points, xG, xGA, shots and xG per shot.
- Compare Liverpool with other teams over the same period; filter by the last five or eight matches, venue, or red-card status.
- Show transparent performance rules with their metrics, benchmarks, thresholds and interpretation limits.
- Import actual player-role minutes, detect double counting across roles, and inspect rotation concentration in complete matches.
- Export Markdown and JSON reports, plus match IDs for appearance-data collection.
- Run the analysis core and tests using the Python standard library, or explore results in a local Streamlit dashboard.

## Quick start

The reference interpreter is Python 3.12.6, recorded in `.python-version`. On macOS or Linux, run these commands in the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python scripts/fetch_data.py --manifest reproducibility/baseline.json
python -m streamlit run app.py
```

On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1`, or invoke its Python executable directly.

No API key or paid account is required. The initial download requires network access; a local snapshot can then be analyzed offline.

To test and reproduce the reference report:

```bash
make test
make reproduce
```

`make reproduce` verifies the input snapshot and three output files against their SHA-256 hashes, then records the code revision and runtime environment separately. Running `python scripts/fetch_data.py` without `--manifest` downloads the current upstream file. The manifest option requires an exact match with the frozen input for this version.

If upstream data changes, restore the archived input rather than treating the latest download as the old snapshot. The dependency lock pins package versions, but not operating-system images or platform wheels. See [Reproducibility](docs/REPRODUCIBILITY.md).

### Generate reports without the dashboard

```bash
python3 scripts/fetch_data.py --manifest reproducibility/baseline.json
python3 scripts/report.py
python3 scripts/report.py --exclude-red --output reports/no-red
```

Outputs are `reports/report.md`, `reports/report.json` and `reports/match_ids.csv`. Use `--as-of YYYY-MM-DD` for an earlier cutoff within the same season.

If the download fails, save the [source CSV](https://www.football-data.co.uk/mmz4281/2627/E0.csv) to `data/local/E0-2627.csv`, or upload a file in the same format in the dashboard. Do not substitute a different season.

## Add appearance data

The match CSV does not contain player appearances, injuries or tactical roles. Position-level assessments therefore default to **Insufficient evidence**.

1. Generate a report or download `match_ids.csv` from the dashboard.
2. Copy `data/templates/appearances.csv`.
3. Use reliable match records to enter each player's actual role, regulation-time minutes and source URL.
4. Upload the appearance file, or run:

```bash
python3 scripts/report.py --appearances path/to/appearances.csv
```

| Field | Meaning |
|---|---|
| match_id | Use an ID exported by the program without changing it |
| player_id | Stable player identifier; do not merge different players with the same name |
| player_name | Player name |
| role | GK / CB / LB / RB / DM / CM / AM / LW / RW / ST |
| minutes | Regulation-time minutes in this role, greater than 0 and no greater than 90 |
| source_url | A traceable source supporting this record |

Split minutes when a player changes role; their total across roles must not exceed 90 in one match. Combine separate segments in the same role before importing. A starting lineup alone is not a complete appearance record, and a registered position is not necessarily the player's match role.

Only matches with no red cards and 990 recorded team minutes count as complete. This is a minimum completeness check, not independent verification of the source. Red-card timelines have not been reconstructed, so those matches are excluded from role-concentration checks.

## Interpret the rules

Rules produce **signals for review**, not trained predictions or causal conclusions.

| Signal | Current trigger |
|---|---|
| Chance creation | xG per match below 90% of the other-team benchmark |
| Chance prevention | xGA per match above 110% of the other-team benchmark |
| Shot quality | xG per shot below 90% of the other-team benchmark |
| Concentrated role usage | One player supplies at least 85% of role minutes; at least eight complete matches cover 80% of selected eligible matches; the role appears in at least eight complete matches |

Each of the first three rules requires eight valid matches for its own metric. These are reviewable initial heuristics, not significance tests or validated predictive thresholds.

- Missing values are not zero. xG differentials use matches with valid xG for both sides.
- Recent-N matches are selected before red-card exclusions, preserving the meaning of the window.
- The benchmark is weighted by other teams' match appearances, includes their matches against Liverpool, and is not adjusted for opponent strength.
- Keep xG model definitions consistent. This project uses one provider, which does not identify a specific model version in its file.
- Concentrated minutes may reflect ability, availability, tactics or selection. Unused backups are not necessarily incapable.
- For shared roles such as CB or CM, shares use all minutes in the role and do not directly measure backup depth.
- An absence of signals does not prove that the squad has no weaknesses. Team xGA cannot automatically be attributed to a center-back or goalkeeper.

See [Methodology](docs/methodology.md) for the decision framework and remaining work.

## Project structure

```text
app.py                    Local dashboard
audit.py                  Validation, statistics, rules and reporting
scripts/fetch_data.py     Source download and provenance
scripts/report.py         Report export without third-party dependencies
scripts/reproduce.py      Frozen-input and output verification
data/templates/           Player-role minute template
data/local/               Local inputs, excluded from Git
reproducibility/           Baseline hashes and reference environment
docs/                     Methodology, reproduction and upload guides
tests/                    Analysis and reproduction checks
```

## Validation

```bash
python3 -m unittest discover -s tests -v
```

Tests use explicitly named synthetic players and matches, never as evidence about Liverpool.

## Publish to GitHub

The local project already contains Git history, with initial features imported separately and subsequent reproducibility improvements committed individually. Use this folder or clone the Git bundle to preserve that history. Web uploads and ordinary source ZIP files do not include it.

Create an [empty GitHub repository](https://github.com/new?name=liverpool-squad-audit) under `Zhecen-Zhou0309`, named `liverpool-squad-audit`. Choose its visibility and leave README, license and `.gitignore` initialization disabled.

From the existing local repository:

```bash
git remote -v
git push -u origin main
git push origin v0.1.1
```

The local origin is configured as `https://github.com/Zhecen-Zhou0309/liverpool-squad-audit.git`. A clone from the bundle needs `git remote set-url origin` before pushing. If `git status` reports that an extracted source ZIP is not a repository, use the bundle to restore history.

System Git authentication is separate from the connected GitHub app. If push requires authentication, use GitHub Desktop or a configured SSH key or credential manager. See the [GitHub guide](docs/GITHUB.md).

Check `git status` before publishing. Raw data, virtual environments, credentials and generated reports are excluded by `.gitignore`. This is an independent repository; GitHub Pages is not needed to run the Python dashboard locally.

See [Contributing](CONTRIBUTING.md) for future changes. Each commit should explain a verifiable change; reproducibility also requires a preserved input and a recorded environment.

## Sources

- [Football-Data.co.uk: England data](https://www.football-data.co.uk/englandm.php)
- [2026–27 Premier League CSV](https://www.football-data.co.uk/mmz4281/2627/E0.csv)
- [Field definitions and upstream acknowledgements](https://www.football-data.co.uk/notes.txt)
- [Liverpool FC official fixtures](https://www.liverpoolfc.com/matches/mens-team/fixtures)

The analysis reads results and match statistics and ignores odds fields. Third-party data is not covered by the source-code license. Source archives exclude the raw match CSV.

This independent project is not affiliated with Liverpool FC.
