import csv
import io
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit import analyze, read_appearances, read_matches, summarize


def raw_match(day="23/08/2026", **changes):
    row = {"Div": "E0", "Date": day, "HomeTeam": "Other", "AwayTeam": "Liverpool",
           "FTHG": "0", "FTAG": "2", "HxG": "0.5", "AxG": "1.5",
           "HS": "8", "AS": "12", "HST": "2", "AST": "4", "HR": "0", "AR": "0"}
    return {**row, **changes}


class AuditTests(unittest.TestCase):
    def load(self, rows):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "matches.csv"
            with path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            return read_matches(path)

    def appearance_csv(self, rows):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["match_id", "player_id", "player_name", "role", "minutes", "source_url"])
        writer.writerows(rows)
        return output.getvalue()

    def test_away_perspective_is_reversed(self):
        report = analyze(self.load([raw_match()]))
        self.assertEqual(report["summary"]["goals_for_total"], 2)
        self.assertEqual(report["summary"]["xg_for_per_match"], 1.5)
        self.assertEqual(report["matches"][0]["venue"], "A")

    def test_missing_xg_is_not_zero_and_differentials_use_pairs(self):
        records = self.load([raw_match(AxG=""), raw_match("24/08/2026", HxG="", AxG="2")])
        report = analyze(records)
        self.assertEqual(report["summary"]["xg_for_per_match"], 2)
        self.assertEqual(report["summary"]["xg_for_n"], 1)
        self.assertIsNone(report["summary"]["xgd_per_match"])
        self.assertEqual(report["signals"], [])

    def test_future_and_unplayed_matches_are_excluded(self):
        records = self.load([raw_match(), raw_match("12/11/2026"), raw_match("11/11/2026", FTHG="", FTAG="")])
        self.assertEqual(analyze(records)["summary"]["matches"], 1)

    def test_red_card_unknown_does_not_mean_no_red(self):
        records = self.load([raw_match(HR=""), raw_match("24/08/2026", AR="1"), raw_match("25/08/2026")])
        report = analyze(records, exclude_red=True)
        self.assertEqual(report["summary"]["matches"], 1)
        self.assertEqual(report["matches"][0]["date"], "2026-08-25")

    def test_recent_window_selected_before_red_filter(self):
        records = self.load([raw_match(), raw_match("24/08/2026", AR="1")])
        report = analyze(records, last_n=1, exclude_red=True)
        self.assertEqual(report["summary"]["matches"], 0)
        self.assertIsNone(report["summary"]["xg_for_per_match"])

    def test_duplicates_nonfinite_and_impossible_stats_rejected(self):
        for rows in ([raw_match(), raw_match()], [raw_match(AxG="nan")], [raw_match(AST="13")], [raw_match(FTAG="")]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                self.load(rows)

    def test_minimum_sample_blocks_signals(self):
        records = self.load([raw_match(AxG="0.01", HxG="8")])
        self.assertEqual(analyze(records)["signals"], [])

    def test_rules_trigger_with_sufficient_synthetic_evidence(self):
        rows = [raw_match((date(2026, 8, 23) + timedelta(days=i)).strftime("%d/%m/%Y"), AxG="0.1", HxG="3") for i in range(8)]
        signals = analyze(self.load(rows))["signals"]
        self.assertIn("xg_for_per_match", {s["id"] for s in signals})
        self.assertTrue(all("validate with video" in s["status"] for s in signals))

    def test_multirole_minutes_cannot_double_count(self):
        records = self.load([raw_match()])
        match_id = records[0]["match_id"]
        text = self.appearance_csv([[match_id, "1", "Synthetic A", "RB", 60, "https://example.org/test"],
                                    [match_id, "1", "Synthetic A", "DM", 60, "https://example.org/test"]])
        with self.assertRaises(ValueError):
            read_appearances(text, records)

    def test_partial_lineups_do_not_trigger_rotation_priority(self):
        records = self.load([raw_match()])
        text = self.appearance_csv([[records[0]["match_id"], "1", "Synthetic A", "RW", 90, "https://example.org/test"]])
        report = analyze(records, appearances=read_appearances(text, records))
        self.assertEqual(report["roles"]["complete_matches"], 0)
        self.assertTrue(all(r["review_priority"] == "Insufficient evidence" for r in report["roles"]["rows"]))

    def test_complete_lineups_allow_concentration_review(self):
        records = self.load([raw_match((date(2026, 8, 23) + timedelta(days=i)).strftime("%d/%m/%Y")) for i in range(8)])
        rows = []
        roles = ["GK", "CB", "CB", "LB", "RB", "DM", "CM", "CM", "LW", "RW", "ST"]
        for record in records:
            if record["team"] != "Liverpool":
                continue
            for i, role in enumerate(roles):
                rows.append([record["match_id"], str(i), f"Synthetic {i}", role, 90, "https://example.org/test"])
        report = analyze(records, appearances=read_appearances(self.appearance_csv(rows), records))
        self.assertEqual(report["roles"]["complete_matches"], 8)
        rw = next(r for r in report["roles"]["rows"] if r["role"] == "RW")
        self.assertEqual(rw["review_priority"], "Review rotation first")
        self.assertEqual(rw["top_share"], 1)

    def test_empty_summary_preserves_missing_values(self):
        result = summarize([])
        self.assertIsNone(result["goals_for_total"])
        self.assertIsNone(result["xg_per_shot"])


if __name__ == "__main__":
    unittest.main()
