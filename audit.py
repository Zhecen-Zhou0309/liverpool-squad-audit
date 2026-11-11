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
    "GK": "门将", "CB": "中后卫", "LB": "左后卫", "RB": "右后卫",
    "DM": "防守中场", "CM": "中前卫", "AM": "进攻中场",
    "LW": "左边锋", "RW": "右边锋", "ST": "中锋",
}
MIN_MATCHES = 8
SOURCE_URL = "https://www.football-data.co.uk/mmz4281/2627/E0.csv"


def number(value, label, *, integer=False):
    if value is None or not str(value).strip():
        return None
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} 必须为数字") from exc
    if not math.isfinite(result) or result < 0 or (integer and not result.is_integer()):
        raise ValueError(f"{label} 必须为非负{'整数' if integer else '有限数字'}")
    return int(result) if integer else result


def read_matches(path: Path | str, as_of=DEFAULT_AS_OF):
    """Read football-data.co.uk E0 CSV; keep both perspectives for benchmarks."""
    if not SEASON_START <= as_of <= SEASON_END:
        raise ValueError("截止日期须位于 2026-08-01 至 2027-06-30")
    records, seen = [], set()
    with Path(path).open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {"Div", "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"}
        if not required <= set(reader.fieldnames or []):
            raise ValueError("比赛 CSV 缺少字段：" + ", ".join(sorted(required - set(reader.fieldnames or []))))
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
                    raise ValueError(f"第 {line} 行比赛日期无效") from exc
            if played < SEASON_START or played > min(as_of, SEASON_END):
                continue
            if row["Div"].strip() != "E0":
                raise ValueError(f"第 {line} 行不是英超 E0 数据")
            home, away = row["HomeTeam"].strip(), row["AwayTeam"].strip()
            if not home or not away or home == away:
                raise ValueError(f"第 {line} 行球队名称无效")
            hg = number(row["FTHG"], "主队进球", integer=True)
            ag = number(row["FTAG"], "客队进球", integer=True)
            if hg is None and ag is None:  # scheduled match, not a 0–0 result
                continue
            if hg is None or ag is None:
                raise ValueError(f"第 {line} 行比分不完整")
            match_id = f"{played.isoformat()}|{home}|{away}"
            if match_id in seen:
                raise ValueError(f"重复比赛：{match_id}")
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
                        raise ValueError(f"{match_id} 射正次数超过射门次数")
                records.append(record)
    if not any(r["team"] == TEAM for r in records):
        raise ValueError("所选范围没有 Liverpool 的已完成比赛；请核对赛季和数据文件")
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
        raise ValueError("出场 CSV 缺少字段：" + ", ".join(sorted(required - set(reader.fieldnames or []))))
    valid = {r["match_id"] for r in matches if r["team"] == TEAM}
    seen, records, totals, match_totals, names = set(), [], defaultdict(float), defaultdict(float), {}
    for line, row in enumerate(reader, 2):
        if not any(row.values()):
            continue
        row = {k: (v or "").strip() for k, v in row.items() if k is not None}
        if row["match_id"] not in valid:
            raise ValueError(f"第 {line} 行 match_id 不属于截止日期内的利物浦比赛")
        if row["role"] not in ROLES:
            raise ValueError(f"第 {line} 行位置须为：{', '.join(ROLES)}")
        if not row["player_id"] or not row["player_name"]:
            raise ValueError(f"第 {line} 行缺少球员标识或姓名")
        if row["player_id"] in names and names[row["player_id"]] != row["player_name"]:
            raise ValueError(f"第 {line} 行同一 player_id 对应不同姓名")
        names[row["player_id"]] = row["player_name"]
        if not row["source_url"].startswith(("https://", "http://")):
            raise ValueError(f"第 {line} 行须提供可追溯的来源 URL")
        minutes = number(row["minutes"], "出场分钟")
        if minutes is None or minutes <= 0 or minutes > 90:
            raise ValueError(f"第 {line} 行分钟须大于 0 且不超过 90")
        key = (row["match_id"], row["player_id"], row["role"])
        if key in seen:
            raise ValueError(f"第 {line} 行重复球员位置；请先合并同一位置的分钟")
        seen.add(key)
        totals[key[:2]] += minutes
        match_totals[key[0]] += minutes
        if totals[key[:2]] > 90.01:
            raise ValueError(f"第 {line} 行同一球员多位置分钟之和超过 90，可能重复计算")
        if match_totals[key[0]] > 990.1:
            raise ValueError(f"第 {line} 行球队总分钟超过 11×90")
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
            "top_share": share, "review_priority": "优先核查轮换" if concentrated else "常规核查" if enough else "证据不足",
            "evidence": "主力承担该位置至少 85% 分钟；需补充替补能力和可用性证据" if concentrated else "仅统计已完整录入、双方无红牌的比赛；未使用球员不等于无法胜任",
        })
    return {"complete_matches": len(complete), "eligible_matches": len(eligible), "coverage": coverage, "rows": rows}


def analyze(records, as_of=DEFAULT_AS_OF, *, exclude_red=False, venue="ALL", last_n=None, appearances=None):
    # Recent-N is selected before red-card exclusions, so it really means last N fixtures.
    own_all = [r for r in records if r["team"] == TEAM and r["date"] <= as_of.isoformat()]
    if last_n is not None:
        if last_n <= 0:
            raise ValueError("最近场数须大于 0")
        own_all = own_all[-last_n:]
    if venue not in {"ALL", "H", "A"}:
        raise ValueError("主客场须为 ALL、H 或 A")
    start = own_all[0]["date"] if own_all else as_of.isoformat()
    def keep(r):
        return r["date"] <= as_of.isoformat() and r["date"] >= start and (venue == "ALL" or r["venue"] == venue) and (not exclude_red or r["red_card_match"] is False)
    own = [r for r in own_all if keep(r)]
    peers = [r for r in records if r["team"] != TEAM and keep(r)]
    summary, benchmark = summarize(own), summarize(peers)
    signals = []
    for field, factor, direction, title, interpretation in (
        ("xg_for_per_match", 0.9, "low", "机会创造值得核查", "复核进攻组织、推进与接应角色；无法仅凭球队 xG 指定需要引进的位置"),
        ("xg_against_per_match", 1.1, "high", "限制对手机会值得核查", "复核转换保护、禁区防守和整体站位；球队 xGA 不能归因给某一位后卫"),
        ("xg_per_shot", 0.9, "low", "射门质量值得核查", "复核射门位置和进攻选择；低单次射门 xG 不代表中锋终结能力差"),
    ):
        count_key = field.replace("_per_match", "") + "_n" if field.endswith("_per_match") else field + "_n"
        actual, base = summary[field], benchmark[field]
        eligible = summary.get(count_key, 0) >= MIN_MATCHES and benchmark.get(count_key, 0) >= MIN_MATCHES
        if actual is None or base is None or base <= 0 or not eligible:
            continue
        triggered = actual < base * factor if direction == "low" else actual > base * factor
        if triggered:
            signals.append({"id": field, "title": title, "actual": actual, "benchmark": base,
                            "rule": f"{'低于' if direction == 'low' else '高于'}其他球队同期均值的 {factor:.0%}",
                            "interpretation": interpretation, "status": "描述性线索，待录像和角色数据验证"})
    return {
        "team": TEAM, "season": "2026–27", "as_of": as_of.isoformat(),
        "filters": {"exclude_red": exclude_red, "venue": venue, "last_n": last_n},
        "summary": summary, "benchmark": benchmark, "matches": own, "signals": signals,
        "roles": role_audit(appearances or [], own),
        "limits": [
            "仅英超；杯赛、欧战负荷尚未纳入。红牌筛选排除整场，不能重建 11 对 11 时段。",
            "其他球队同期均值按球队场次加权；包含对阵利物浦的记录，未校正对手强弱、比分状态、赛程和战术。",
            "xG 为数据源的模型输出，不是预期比分。缺失值保留为空，绝不当作 0。",
            "8 场门槛与 90%/110% 阈值是可审查的启发式规则，未经预测验证，不是显著性或因果结论。",
            "位置轮换集中不等于人员不足；伤停、替补能力、阵型与事件区域证据仍需补齐。",
        ],
        "source_url": SOURCE_URL,
    }


def fmt(value, digits=2):
    return "缺失" if value is None else f"{value:.{digits}f}"


def to_markdown(report):
    s = report["summary"]
    filters = report["filters"]
    scope = "赛季至今" if filters["last_n"] is None else f"最近 {filters['last_n']} 场"
    venue = {"ALL": "全部主客场", "H": "主场", "A": "客场"}[filters["venue"]]
    red = "排除出现红牌的整场比赛" if filters["exclude_red"] else "包含红牌比赛"
    lines = [f"# 利物浦阵容诊断 · {report['season']}", "", f"截止日期：{report['as_of']}（含当天已完成比赛）", "",
             f"筛选：{scope}；{venue}；{red}。", "",
             f"样本：{s['matches']} 场，{s['wins']} 胜 {s['draws']} 平 {s['losses']} 负。", "",
             "| 指标 | 利物浦 | 其他球队同期均值 | 有效比赛数（利物浦） |", "|---|---:|---:|---:|"]
    for field, name in (("goals_for", "场均进球"), ("goals_against", "场均失球"), ("xg_for", "场均 xG"), ("xg_against", "场均 xGA"), ("shots_for", "场均射门")):
        lines.append(f"| {name} | {fmt(s[field+'_per_match'])} | {fmt(report['benchmark'][field+'_per_match'])} | {s[field+'_n']} |")
    lines += ["", "## 比赛线索", ""]
    if not report["signals"]:
        lines += ["当前筛选下没有触发规则，或有效样本未达到 8 场；这不表示阵容没有缺陷。", ""]
    for signal in report["signals"]:
        lines += [f"- **{signal['title']}**：{fmt(signal['actual'])}，同期基准 {fmt(signal['benchmark'])}；规则：{signal['rule']}。{signal['interpretation']}。", ""]
    roles = report["roles"]
    lines += ["## 阵容证据", "", f"完整出场数据：{roles['complete_matches']}/{roles['eligible_matches']} 场（双方无红牌且已知红牌状态）。", "",
              "当前系统只输出位置核查优先级，不自动认定应买哪个位置。", "",
              "| 位置 | 已用人数 | 主力分钟占比 | 核查优先级 |", "|---|---:|---:|---|"]
    for r in roles["rows"]:
        share = "缺失" if r["top_share"] is None else f"{r['top_share']:.1%}"
        lines.append(f"| {r['name']} | {r['players_used'] if r['minutes'] else '缺失'} | {share} | {r['review_priority']} |")
    lines += ["", "## 解释限制", ""] + [f"- {limit}" for limit in report["limits"]]
    lines += ["", f"数据来源：[Football-Data.co.uk]({report['source_url']})", ""]
    if report.get("input_sha256"):
        lines += [f"输入快照 SHA-256：`{report['input_sha256']}`", ""]
    return "\n".join(lines)
