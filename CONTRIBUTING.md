# Contributing

Each commit should solve a clear problem so analysis changes can be traced to specific code. Run relevant checks before committing; avoid empty changes intended only to increase the count.

## Workflow

```bash
git switch main
git pull --ff-only
git switch -c feat/appearance-import
```

After completing a functional change, inspect the diff and commit it:

```bash
python -m unittest discover -s tests -v
git diff
git add scripts/new_importer.py tests/test_new_importer.py
git commit -m "feat: import verified player appearances"
git push -u origin feat/appearance-import
```

Replace the example filenames with files you actually changed. Explain the problem, resulting behavior and validation in the pull request. Choose a merge method that preserves individual commits if that history should remain on main; squash merging consolidates them.

## Suggested next tasks

- Import verified Liverpool appearances, starting lineups, substitutions and regulation-time minutes.
- Map formations to actual roles and handle changes within a match.
- Build a separate roster and backup-coverage model without counting one versatile player twice in a scenario.
- Add dated availability records with explicit injury, suspension and selection categories.
- Add event-location or video evidence for transition defending and chance creation.
- Produce recruitment role profiles supported by complete evidence.
- Evaluate thresholds through historical backtests and sensitivity analysis.

## Commit messages

Use `feat:` for features, `fix:` for fixes, `test:` for meaningful checks, `docs:` for documentation, `build:` for environments, and `ci:` for automation.

Keep unrelated data, algorithm and interface changes separate. Preserve old baselines and explain model or input-snapshot updates.
