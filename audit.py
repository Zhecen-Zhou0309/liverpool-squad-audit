"""Explainable, descriptive squad audit. The analysis core uses only Python stdlib."""
from __future__ import annotations

import csv
import io
import math
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from statistics import mean

TEAM = "Liverpool"
DEFAULT_AS_OF = date(2026, 11, 11)
SEASON_START = date(2026, 8, 1)
SEASON_END = date(2027, 6, 30)
ROLES = {
    "GK": "Goalkeeper", "CB": "Center-back", "LB": "Left-back", "RB": "Right-back",
    "DM": "Defensive midfielder", "CM": "Central midfielder", "AM": "Attacking midfielder",
    "LW": "Left winger", "RW": "Right winger", "ST": "Striker",
}
MIN_MATCHES = 8
SOURCE_URL = "https://www.football-data.co.uk/mmz4281/2627/E0.csv"


def number(value, label, *, integer=False):
    if value is None or not str(value).strip():
        return None
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(result) or result < 0 or (integer and not result.is_integer()):
        raise ValueError(f"{label} must be a nonnegative {'integer' if integer else 'finite number'}")
    return int(result) if integer else result


def read_matches(path: Path | str, as_of=DEFAULT_AS_OF):
    """Read football-data.co.uk E0 CSV; keep both perspectives for benchmarks."""
    if not SEASON_START <= as_of <= SEASON_END:
        raise ValueError("The cutoff date must fall between 2026-08-01 and 2027-06-30")
    records, seen = [], set()
    with Path(path).open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {"Div", "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"}
        if not required <= set(reader.fieldnames or []):
            raise ValueError("Match CSV is missing fields: " + ", ".join(sorted(required - set(reader.fieldnames or []))))
        for line, row in enumerate(reader, 2):
            if not any(row.values()):
                continue
            raw_date = row["Date"].strip()
            try:
                played = datetime.strptime(raw_date, "%d/%m/%Y").date()
            except ValueError:
                try:
                    played = datetime.strptime(raw_date, "%d/%m/%y").date()
                except ValueError as exc:
                    raise ValueError(f"Invalid match date on row {line}") from exc
            if played < SEASON_START or played > min(as_of, SEASON_END):
                continue
            if row["Div"].strip() != "E0":
                raise ValueError(f"Row {line} is not Premier League E0 data")
            home, away = row["HomeTeam"].strip(), row["AwayTeam"].strip()
            if not home or not away or home == away:
                raise ValueError(f"Invalid team names on row {line}")
            hg = number(row["FTHG"], "Home goals", integer=True)
            ag = number(row["FTAG"], "Away goals", integer=True)
            if hg is None and ag is None:  # scheduled match, not a 0–0 result
                continue
            if hg is None or ag is None:
                raise ValueError(f"Incomplete score on row {line}")
            match_id = f"{played.isoformat()}|{home}|{away}"
            if match_id in seen:
                raise ValueError(f"Duplicate match: {match_id}")
            seen.add(match_id)
            hr, ar = (number(row.get(k), k, integer=True) for k in ("HR", "AR"))
            for team, opponent, venue, gf, ga, own, opp in (
                (home, away, "H", hg, ag, "H", "A"),
                (away, home, "A", ag, hg, "A", "H"),
            ):
                record = {
                    "match_id": match_id, "date": played.isoformat(), "team": team,
                    "opponent": opponent, "venue": venue, "goals_for": gf,
                    "goals_against": ga, "points": 3 if gf > ga else 1 if gf == ga else 0,
                    "red_card_match": None if hr is None or ar is None else hr + ar > 0,
                }
                for target, column in (
                    ("xg_for", own + "xG"), ("xg_against", opp + "xG"),
                    ("shots_for", own + "S"), ("shots_against", opp + "S"),
                    ("sot_for", own + "ST"), ("sot_against", opp + "ST"),
                ):
                    record[target] = number(row.get(column), column, integer=not target.startswith("xg"))
                for suffix in ("for", "against"):
                    shots, sot = record[f"shots_{suffix}"], record[f"sot_{suffix}"]
                    if shots is not None and sot is not None and sot > shots:
                        raise ValueError(f"Shots on target exceed shots in {match_id}")
                records.append(record)
    if not any(r["team"] == TEAM for r in records):
        raise ValueError("No completed Liverpool matches in this range; check the season and input file")
    return sorted(records, key=lambda r: (r["date"], r["match_id"], r["team"]))


def summarize(records):
    result = {"matches": len(records)}
    for field in ("goals_for", "goals_against", "points", "xg_for", "xg_against", "shots_for", "shots_against", "sot_for", "sot_against"):
        values = [r[field] for r in records if r[field] is not None]
        result[field + "_n"] = len(values)
        result[field + "_total"] = sum(values) if values else None
        result[field + "_per_match"] = mean(values) if values else None
    paired = [r for r in records if r["xg_for"] is not None and r["xg_against"] is not None]
    result["xgd_n"] = len(paired)
    result["xgd_per_match"] = mean(r["xg_for"] - r["xg_against"] for r in paired) if paired else None
    attempts = [r for r in records if r["xg_for"] is not None and r["shots_for"] is not None]
    denominator = sum(r["shots_for"] for r in attempts)
    result["xg_per_shot"] = sum(r["xg_for"] for r in attempts) / denominator if denominator else None
    result["xg_per_shot_n"] = len(attempts)
    result["wins"] = sum(r["points"] == 3 for r in records)
    result["draws"] = sum(r["points"] == 1 for r in records)
    result["losses"] = sum(r["points"] == 0 for r in records)
    return result


def read_appearances(text, matches):
    """One row per player's role segment; minutes exclude stoppage time (0–90)."""
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    required = {"match_id", "player_id", "player_name", "role", "minutes", "source_url"}
    if not required <= set(reader.fieldnames or []):
        raise ValueError("Appearance CSV is missing fields: " + ", ".join(sorted(required - set(reader.fieldnames or []))))
    valid = {r["match_id"] for r in matches if r["team"] == TEAM}
    seen, records, totals, match_totals, names = set(), [], defaultdict(float), defaultdict(float), {}
    for line, row in enumerate(reader, 2):
        if not any(row.values()):
            continue
        row = {k: (v or "").strip() for k, v in row.items() if k is not None}
        if row["match_id"] not in valid:
            raise ValueError(f"Row {line} has a match_id outside Liverpool's in-scope matches")
        if row["role"] not in ROLES:
            raise ValueError(f"Row {line} must use one of these roles: {', '.join(ROLES)}")
        if not row["player_id"] or not row["player_name"]:
            raise ValueError(f"Row {line} is missing a player ID or name")
        if row["player_id"] in names and names[row["player_id"]] != row["player_name"]:
            raise ValueError(f"Row {line} assigns different names to the same player_id")
        names[row["player_id"]] = row["player_name"]
        if not row["source_url"].startswith(("https://", "http://")):
            raise ValueError(f"Row {line} requires a traceable source URL")
        minutes = number(row["minutes"], "Appearance minutes")
        if minutes is None or minutes <= 0 or minutes > 90:
            raise ValueError(f"Minutes on row {line} must be greater than 0 and no greater than 90")
        key = (row["match_id"], row["player_id"], row["role"])
        if key in seen:
            raise ValueError(f"Duplicate player-role entry on row {line}; combine minutes in the same role first")
        seen.add(key)
        totals[key[:2]] += minutes
        match_totals[key[0]] += minutes
        if totals[key[:2]] > 90.01:
            raise ValueError(f"Player minutes across roles exceed 90 on row {line}; check for double counting")
        if match_totals[key[0]] > 990.1:
            raise ValueError(f"Team minutes exceed 11 x 90 on row {line}")
        records.append({**row, "minutes": minutes})
    return records


def role_audit(appearances, matches):
    """Rotation concentration is an observation, never proof of a transfer need."""
    ids = {r["match_id"] for r in matches}
    segments = [a for a in appearances if a["match_id"] in ids]
    minutes_by_match = defaultdict(float)
    for a in segments:
        minutes_by_match[a["match_id"]] += a["minutes"]
    eligible = [r for r in matches if r["red_card_match"] is False]
    complete = {r["match_id"] for r in eligible if abs(minutes_by_match[r["match_id"]] - 990) <= 0.1}
    coverage = len(complete) / len(eligible) if eligible else 0
    rows = []
    for role, name in ROLES.items():
        # Partial matches cannot manufacture an apparently dominant starter.
        by_player, role_matches = defaultdict(float), set()
        for a in segments:
            if a["role"] == role and a["match_id"] in complete:
                by_player[(a["player_id"], a["player_name"]) ] += a["minutes"]
                role_matches.add(a["match_id"])
        ordered = sorted(by_player.items(), key=lambda item: (-item[1], item[0][0]))
        total = sum(by_player.values())
        share = ordered[0][1] / total if total else None
        enough = len(complete) >= MIN_MATCHES and coverage >= 0.8 and len(role_matches) >= MIN_MATCHES
        concentrated = enough and share is not None and share >= 0.85
        rows.append({
            "role": role, "name": name, "players_used": len(by_player),
            "role_matches": len(role_matches), "minutes": total,
            "most_used": ordered[0][0][1] if ordered else None,
            "top_share": share, "review_priority": "Review rotation first" if concentrated else "Routine review" if enough else "Insufficient evidence",
            "evidence": "One player accounts for at least 85% of role minutes; assess backup capability and availability" if concentrated else "Only complete matches without red cards are included; unused players may still be capable backups",
        })
    return {"complete_matches": len(complete), "eligible_matches": len(eligible), "coverage": coverage, "rows": rows}


def analyze(records, as_of=DEFAULT_AS_OF, *, exclude_red=False, venue="ALL", last_n=None, appearances=None):
    # Recent-N is selected before red-card exclusions, so it really means last N fixtures.
    own_all = [r for r in records if r["team"] == TEAM and r["date"] <= as_of.isoformat()]
    if last_n is not None:
        if last_n <= 0:
            raise ValueError("The recent-match count must be greater than 0")
        own_all = own_all[-last_n:]
    if venue not in {"ALL", "H", "A"}:
        raise ValueError("Venue must be ALL, H or A")
    start = own_all[0]["date"] if own_all else as_of.isoformat()
    def keep(r):
        return r["date"] <= as_of.isoformat() and r["date"] >= start and (venue == "ALL" or r["venue"] == venue) and (not exclude_red or r["red_card_match"] is False)
    own = [r for r in own_all if keep(r)]
    peers = [r for r in records if r["team"] != TEAM and keep(r)]
    summary, benchmark = summarize(own), summarize(peers)
    signals = []
    for field, factor, direction, title, interpretation in (
        ("xg_for_per_match", 0.9, "low", "Review chance creation", "Review attacking structure, progression and receiving roles; team xG alone cannot identify a recruitment position"),
        ("xg_against_per_match", 1.1, "high", "Review chance prevention", "Review transition protection, box defending and team positioning; team xGA cannot be attributed to one defender"),
        ("xg_per_shot", 0.9, "low", "Review shot quality", "Review shot locations and attacking decisions; low xG per shot does not establish poor striker finishing"),
    ):
        count_key = field.replace("_per_match", "") + "_n" if field.endswith("_per_match") else field + "_n"
        actual, base = summary[field], benchmark[field]
        eligible = summary.get(count_key, 0) >= MIN_MATCHES and benchmark.get(count_key, 0) >= MIN_MATCHES
        if actual is None or base is None or base <= 0 or not eligible:
            continue
        triggered = actual < base * factor if direction == "low" else actual > base * factor
        if triggered:
            signals.append({"id": field, "title": title, "actual": actual, "benchmark": base,
                            "rule": f"{'Below' if direction == 'low' else 'Above'} {factor:.0%} of the other-team benchmark",
                            "interpretation": interpretation, "status": "Descriptive signal; validate with video and role data"})
    return {
        "team": TEAM, "season": "2026–27", "as_of": as_of.isoformat(),
        "filters": {"exclude_red": exclude_red, "venue": venue, "last_n": last_n},
        "summary": summary, "benchmark": benchmark, "matches": own, "signals": signals,
        "roles": role_audit(appearances or [], own),
        "limits": [
            "Premier League only; cup and European workloads are excluded. The red-card filter removes whole matches, not individual 11-v-11 periods.",
            "The other-team benchmark is weighted by team appearances and includes matches against Liverpool. Opponent strength, score state, scheduling and tactics are not adjusted.",
            "xG is the provider's model output, not a predicted score. Missing values remain missing rather than becoming zero.",
            "The eight-match minimum and 90%/110% thresholds are reviewable heuristics, not validated predictions, significance tests or causal conclusions.",
            "Concentrated role usage does not establish a squad shortage; availability, backup capability, formation and event-location evidence are still needed.",
        ],
        "source_url": SOURCE_URL,
    }


def fmt(value, digits=2):
    return "Missing" if value is None else f"{value:.{digits}f}"


def to_markdown(report):
    s = report["summary"]
    filters = report["filters"]
    scope = "Season to date" if filters["last_n"] is None else f"Last {filters['last_n']} matches"
    venue = {"ALL": "All venues", "H": "Home", "A": "Away"}[filters["venue"]]
    red = "Exclude matches with red cards" if filters["exclude_red"] else "Include matches with red cards"
    lines = [f"# Liverpool Squad Audit · {report['season']}", "", f"Cutoff: {report['as_of']} (including completed matches on this date)", "",
             f"Filters: {scope}; {venue}; {red}.", "",
             f"Sample: {s['matches']} matches; {s['wins']} wins, {s['draws']} draws, {s['losses']} losses.", "",
             "| Metric | Liverpool | Other-team benchmark | Valid Liverpool matches |", "|---|---:|---:|---:|"]
    for field, name in (("goals_for", "Goals per match"), ("goals_against", "Goals conceded per match"), ("xg_for", "xG per match"), ("xg_against", "xGA per match"), ("shots_for", "Shots per match")):
        lines.append(f"| {name} | {fmt(s[field+'_per_match'])} | {fmt(report['benchmark'][field+'_per_match'])} | {s[field+'_n']} |")
    lines += ["", "## Match signals", ""]
    if not report["signals"]:
        lines += ["No rules were triggered under these filters, or fewer than eight valid matches were available. This does not establish that the squad has no weaknesses.", ""]
    for signal in report["signals"]:
        lines += [f"- **{signal['title']}**: {fmt(signal['actual'])}; benchmark {fmt(signal['benchmark'])}; rule: {signal['rule']}. {signal['interpretation']}.", ""]
    roles = report["roles"]
    lines += ["## Squad evidence", "", f"Complete appearance data: {roles['complete_matches']}/{roles['eligible_matches']} matches with confirmed no-red-card status for both teams.", "",
              "The system prioritizes roles for review; it does not automatically identify a position to recruit.", "",
              "| Role | Players used | Leading player's minute share | Review priority |", "|---|---:|---:|---|"]
    for r in roles["rows"]:
        share = "Missing" if r["top_share"] is None else f"{r['top_share']:.1%}"
        lines.append(f"| {r['name']} | {r['players_used'] if r['minutes'] else 'Missing'} | {share} | {r['review_priority']} |")
    lines += ["", "## Interpretation limits", ""] + [f"- {limit}" for limit in report["limits"]]
    lines += ["", f"Data source: [Football-Data.co.uk]({report['source_url']})", ""]
    if report.get("input_sha256"):
        lines += [f"Input snapshot SHA-256: `{report['input_sha256']}`", ""]
    return "\n".join(lines)
