"""Export a report without installing any third-party dependencies."""
import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from audit import DEFAULT_AS_OF, analyze, read_appearances, read_matches, to_markdown  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Generate a Liverpool 2026-27 squad audit report")
    parser.add_argument("--csv", type=Path, default=ROOT / "data/local/E0-2627.csv")
    parser.add_argument("--as-of", type=date.fromisoformat, default=DEFAULT_AS_OF)
    parser.add_argument("--appearances", type=Path)
    parser.add_argument("--exclude-red", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "reports")
    args = parser.parse_args()
    try:
        records = read_matches(args.csv, args.as_of)
        appearances = read_appearances(args.appearances.read_text(encoding="utf-8-sig"), records) if args.appearances else []
        report = analyze(records, args.as_of, exclude_red=args.exclude_red, appearances=appearances)
        report["input_sha256"] = hashlib.sha256(args.csv.read_bytes()).hexdigest()
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "report.md").write_text(to_markdown(report), encoding="utf-8")
        (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        # IDs are provided even when lineup data has not been collected.
        import csv
        with (args.output / "match_ids.csv").open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["match_id", "date", "opponent", "venue"])
            writer.writeheader()
            writer.writerows({k: r[k] for k in writer.fieldnames} for r in report["matches"])
        print(f"Generated {args.output / 'report.md'}")
    except (OSError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
