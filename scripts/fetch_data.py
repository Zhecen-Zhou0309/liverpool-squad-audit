"""Download and validate the current-season snapshot; never silently change seasons."""
import argparse
import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from audit import DEFAULT_AS_OF, SOURCE_URL, read_matches  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Download Premier League data and optionally verify byte identity against a baseline manifest")
    parser.add_argument("--manifest", type=Path, help="Baseline JSON containing source.sha256")
    args = parser.parse_args()
    destination = ROOT / "data/local"
    destination.mkdir(parents=True, exist_ok=True)
    try:
        request = Request(SOURCE_URL, headers={"User-Agent": "LiverpoolSquadAudit/0.1 (research project)"})
        with urlopen(request, timeout=30) as response:
            content = response.read(5_000_001)
        if len(content) > 5_000_000:
            raise ValueError("File exceeds 5 MB; check the data source")
        if args.manifest:
            manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
            if SOURCE_URL != manifest["source"]["url"]:
                raise ValueError("Download URL differs from the baseline manifest")
            if hashlib.sha256(content).hexdigest() != manifest["source"]["sha256"]:
                raise ValueError("The upstream file has changed: SHA-256 differs from the baseline. The existing local snapshot is preserved. Restore archived data or review the changes before creating a new baseline")
        with tempfile.TemporaryDirectory() as temp:
            candidate = Path(temp) / "matches.csv"
            candidate.write_bytes(content)
            records = read_matches(candidate, DEFAULT_AS_OF)
        # Only replace the prior snapshot after validation succeeds.
        (destination / "E0-2627.csv").write_bytes(content)
        metadata = {"source_url": SOURCE_URL, "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "sha256": hashlib.sha256(content).hexdigest(), "season": "2026–27",
                    "latest_in_scope_match": max(r["date"] for r in records), "cutoff": DEFAULT_AS_OF.isoformat()}
        (destination / "provenance.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Downloaded and validated {len(records)//2} Premier League matches through {DEFAULT_AS_OF}.")
    except (OSError, URLError, ValueError, KeyError) as exc:
        raise SystemExit(f"Download failed: {exc}\nNo other season or synthetic data will be substituted. Use the source in the README to download the CSV manually.") from exc


if __name__ == "__main__":
    main()
