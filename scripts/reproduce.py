"""Verify the frozen input and deterministic outputs; preserve run provenance separately."""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_state():
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip())
        return {"commit": commit, "worktree_dirty": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "worktree_dirty": None}


def main():
    parser = argparse.ArgumentParser(description="Verify a frozen input and rebuild baseline reports without network access")
    parser.add_argument("--manifest", type=Path, default=ROOT / "reproducibility/baseline.json")
    parser.add_argument("--csv", type=Path, default=ROOT / "data/local/E0-2627.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/reproduced")
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if not args.csv.exists():
            raise ValueError("Frozen input is missing. Run make data or restore your archived original CSV")
        if sha256(args.csv) != manifest["source"]["sha256"]:
            raise ValueError("Input SHA-256 differs from the baseline; reproduction stopped rather than using updated data as the original version")
        # Report paths are explicit so invocation does not depend on the shell cwd.
        subprocess.run([sys.executable, str(ROOT / "scripts/report.py"), "--csv", str(args.csv.resolve()),
                        "--as-of", manifest["analysis"]["as_of"], "--output", str(args.output.resolve())], check=True)
        hashes = {name: sha256(args.output / name) for name in manifest["outputs"]}
        mismatch = [name for name, expected in manifest["outputs"].items() if hashes[name] != expected]
        metadata = {
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
            "git": git_state(), "python": platform.python_version(),
            "platform": platform.platform(), "dependency_lock_sha256": sha256(ROOT / "requirements.lock"),
            "input_sha256": sha256(args.csv), "outputs": hashes,
            "matches_baseline": not mismatch,
        }
        (args.output / "run_metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if mismatch:
            raise ValueError("Reports differ from the baseline: " + ", ".join(mismatch) + "; review code or environment differences before changing the baseline")
        print("Reproduction passed: the input snapshot and all report SHA-256 hashes match the baseline.")
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"Reproduction failed: {exc}") from exc


if __name__ == "__main__":
    main()
