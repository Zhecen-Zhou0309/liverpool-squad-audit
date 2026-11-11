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
    parser = argparse.ArgumentParser(description="下载英超数据，可按基线清单验证字节级一致性")
    parser.add_argument("--manifest", type=Path, help="包含 source.sha256 的基线 JSON")
    args = parser.parse_args()
    destination = ROOT / "data/local"
    destination.mkdir(parents=True, exist_ok=True)
    try:
        request = Request(SOURCE_URL, headers={"User-Agent": "LiverpoolSquadAudit/0.1 (research project)"})
        with urlopen(request, timeout=30) as response:
            content = response.read(5_000_001)
        if len(content) > 5_000_000:
            raise ValueError("文件超过 5MB，请检查数据源")
        if args.manifest:
            manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
            if SOURCE_URL != manifest["source"]["url"]:
                raise ValueError("下载地址与基线清单不同")
            if hashlib.sha256(content).hexdigest() != manifest["source"]["sha256"]:
                raise ValueError("源站文件已变动，SHA-256 与基线不一致；保留已有本地快照。请恢复归档数据，或审查后建立新的分析基线")
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
        print(f"下载并验证完成：{len(records)//2} 场英超比赛；截止 {DEFAULT_AS_OF}。")
    except (OSError, URLError, ValueError, KeyError) as exc:
        raise SystemExit(f"下载未完成：{exc}\n不会用其他赛季或模拟数据替代。可从 README 中的来源手动下载 CSV。") from exc


if __name__ == "__main__":
    main()
