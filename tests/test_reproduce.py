"""Synthetic offline fixtures test exact-input/output verification, not live scores."""
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReproductionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.csv = self.folder / "synthetic.csv"
        with self.csv.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Div", "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"])
            writer.writerow(["E0", "23/08/2026", "Synthetic FC", "Liverpool", "0", "1"])
        expected = self.folder / "expected"
        result = subprocess.run([sys.executable, str(ROOT / "scripts/report.py"), "--csv", str(self.csv), "--output", str(expected)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.manifest = {"source": {"sha256": hashlib.sha256(self.csv.read_bytes()).hexdigest()},
                         "analysis": {"as_of": "2026-11-11"},
                         "outputs": {name: hashlib.sha256((expected / name).read_bytes()).hexdigest()
                                     for name in ("report.md", "report.json", "match_ids.csv")}}
        self.manifest_path = self.folder / "manifest.json"

    def run_reproduction(self):
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        return subprocess.run([sys.executable, str(ROOT / "scripts/reproduce.py"), "--manifest", str(self.manifest_path),
                               "--csv", str(self.csv), "--output", str(self.folder / "actual")],
                              cwd=self.folder, capture_output=True, text=True)

    def test_reproduces_from_a_different_working_directory(self):
        result = self.run_reproduction()
        self.assertEqual(result.returncode, 0, result.stderr)
        metadata = json.loads((self.folder / "actual/run_metadata.json").read_text())
        self.assertTrue(metadata["matches_baseline"])
        self.assertEqual(metadata["input_sha256"], self.manifest["source"]["sha256"])

    def test_changed_input_fails_before_report_generation(self):
        self.csv.write_bytes(self.csv.read_bytes() + b"\n")
        result = self.run_reproduction()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("输入 SHA-256", result.stderr)
        self.assertFalse((self.folder / "actual/report.json").exists())

    def test_changed_expected_output_fails_and_records_the_mismatch(self):
        self.manifest["outputs"]["report.json"] = "0" * 64
        result = self.run_reproduction()
        self.assertNotEqual(result.returncode, 0)
        metadata = json.loads((self.folder / "actual/run_metadata.json").read_text())
        self.assertFalse(metadata["matches_baseline"])


if __name__ == "__main__":
    unittest.main()
