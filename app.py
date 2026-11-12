"""Local Streamlit dashboard. Run: python -m streamlit run app.py"""
import hashlib
import json
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from audit import DEFAULT_AS_OF, SOURCE_URL, analyze, fmt, read_appearances, read_matches, to_markdown

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Liverpool · Squad Audit", page_icon="⚽", layout="wide")
st.markdown("""<style>
.block-container {max-width:1260px;padding-top:2.2rem}
h1 {letter-spacing:-.045em;font-weight:750 !important}
[data-testid="stMetric"] {background:#fff;border:1px solid #e5e4df;border-radius:12px;padding:18px}
[data-testid="stMetricLabel"] {color:#64716d}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### LIVERPOOL\nSquad Audit")
    st.caption("2026–27 · Phase One")
    st.write(f"Fixed cutoff: {DEFAULT_AS_OF}")
    window = st.selectbox("Match window", ["Season to date", "Last 8 matches", "Last 5 matches"])
    venue_name = st.selectbox("Venue", ["All", "Home", "Away"])
    exclude_red = st.checkbox("Exclude matches with a red card for either team", value=False)
    st.divider()
    st.caption("Use a downloaded local file or upload data in the same format.")
    uploaded = st.file_uploader("Match CSV (Football-Data E0 format)", type=["csv"])
    lineup = st.file_uploader("Player appearance CSV (optional)", type=["csv"])
    st.download_button("Download appearance template", (ROOT / "data/templates/appearances.csv").read_bytes(), "appearances.csv", "text/csv")

st.caption("FOOTBALL INTELLIGENCE / 01")
st.title("Where does Liverpool need reinforcements?")
st.write("Build evidence from match performance and role coverage to guide recruitment priorities.")
st.caption("Premier League only. Role-level recommendations require complete appearance and squad evidence.")

try:
    if uploaded is not None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "uploaded.csv"
            path.write_bytes(uploaded.getvalue())
            records = read_matches(path)
        input_label = "User-uploaded CSV (not independently verified)"
    else:
        path = ROOT / "data/local/E0-2627.csv"
        if not path.exists():
            st.info("Match data has not been downloaded. Run this command in the project directory, then refresh.")
            st.code("python scripts/fetch_data.py", language="bash")
            st.markdown(f"Alternatively, [download the match CSV]({SOURCE_URL}) and upload it in the sidebar.")
            st.stop()
        records = read_matches(path)
        input_label = "Local Football-Data.co.uk snapshot"
    appearances = read_appearances(lineup.getvalue().decode("utf-8-sig"), records) if lineup else []
    report = analyze(records, exclude_red=exclude_red,
                     venue={"All": "ALL", "Home": "H", "Away": "A"}[venue_name],
                     last_n={"Season to date": None, "Last 8 matches": 8, "Last 5 matches": 5}[window],
                     appearances=appearances)
except (OSError, UnicodeError, ValueError) as exc:
    st.error(f"Data validation failed: {exc}")
    st.stop()

report["input_label"] = input_label
report["input_sha256"] = hashlib.sha256(uploaded.getvalue() if uploaded is not None else path.read_bytes()).hexdigest()
s, b = report["summary"], report["benchmark"]
columns = st.columns(4)
columns[0].metric("Matches analyzed", s["matches"], f"{s['wins']} W · {s['draws']} D · {s['losses']} L", delta_color="off")
columns[1].metric("Points", fmt(s["points_total"], 0))
columns[2].metric("xG per match · Chance creation", fmt(s["xg_for_per_match"]))
columns[3].metric("xGA per match · Chances conceded", fmt(s["xg_against_per_match"]))
if s["matches"] < 8:
    st.warning("Fewer than eight matches selected. Statistics remain available; recruitment-related rules are paused.")

matches_tab, squad_tab, diagnosis_tab, source_tab = st.tabs(["Match performance", "Squad coverage", "Diagnosis and evidence", "Data and methods"])
with matches_tab:
    st.subheader("Chance creation and defensive risk")
    st.caption("xG means expected goals; xGA is the opponent's expected goals. These describe shooting chances, not predicted scores.")
    if report["matches"]:
        frame = pd.DataFrame(report["matches"])
        trend = frame.set_index("date")[["xg_for", "xg_against"]].rename(columns={"xg_for": "Liverpool xG", "xg_against": "Opponent xG"})
        st.line_chart(trend, color=["#c8102e", "#177e72"])
        evidence = frame[["date", "match_id", "opponent", "venue", "goals_for", "goals_against", "xg_for", "xg_against", "shots_for", "shots_against", "red_card_match"]]
        st.dataframe(evidence.rename(columns={"date": "Date", "opponent": "Opponent", "venue": "Venue", "goals_for": "Goals", "goals_against": "Goals conceded", "xg_for": "xG", "xg_against": "xGA", "shots_for": "Shots", "shots_against": "Opponent shots", "red_card_match": "Red card in match"}), hide_index=True)
        st.download_button("Download match IDs for appearance data", frame[["match_id", "date", "opponent", "venue"]].to_csv(index=False), "match_ids.csv", "text/csv")
    else:
        st.info("No matches under the current filters.")
    st.subheader("League benchmark for the same period")
    comparison = []
    for key, label in (("goals_for", "Goals per match"), ("goals_against", "Goals conceded per match"), ("xg_for", "xG per match"), ("xg_against", "xGA per match"), ("shots_for", "Shots per match")):
        comparison.append({"Metric": label, "Liverpool": s[key + "_per_match"], "Other teams": b[key + "_per_match"], "Valid matches": s[key + "_n"]})
    st.dataframe(pd.DataFrame(comparison), hide_index=True)
    st.caption("The benchmark uses the same period and filters without opponent-strength adjustment. Missing values remain missing, not zero.")

with squad_tab:
    roles = report["roles"]
    st.subheader("Role coverage and rotation concentration")
    st.write(f"Complete appearance records: {roles['complete_matches']} / {roles['eligible_matches']} matches without red cards for either team.")
    if not appearances:
        st.info("No player appearance data loaded. Download the template, record actual role minutes and sources for each match, then upload it.")
    st.caption("Split minutes when a player changes role. This table cannot assess unused backups. Red-card matches are excluded from completeness checks.")
    rows = [{"Role": r["name"], "Players used": r["players_used"] if r["minutes"] else None,
             "Complete matches with role": r["role_matches"], "Most-used player": r["most_used"],
             "Leading player's minute share": r["top_share"], "Review priority": r["review_priority"]} for r in roles["rows"]]
    st.dataframe(pd.DataFrame(rows), hide_index=True)
    with st.expander("Preparing appearance data"):
        st.write("Download match IDs from Match performance and fill the template. Use regulation-time minutes from 0 to 90, excluding stoppage time. A player's minutes across roles must not exceed 90 in one match.")
        st.write("A match is complete only with 990 team minutes and no red cards. Rotation checks require at least eight complete matches covering 80% of selected eligible matches. A leading player with at least 85% of role minutes is flagged for review.")
        st.write("For roles shared by multiple players, such as center-back, shares use all minutes in that role. They do not measure formation slots or backup depth.")

with diagnosis_tab:
    st.subheader("Evidence behind recruitment decisions")
    for signal in report["signals"]:
        with st.container(border=True):
            st.markdown(f"**{signal['title']}**")
            st.write(f"Liverpool: {fmt(signal['actual'])} / benchmark: {fmt(signal['benchmark'])}. Trigger: {signal['rule']}.")
            st.write(signal["interpretation"])
            st.caption(signal["status"])
    if not report["signals"]:
        st.info("No match-signal rule was triggered, or the valid sample is too small. This does not establish that the squad has no weaknesses.")
    concentrated = [r for r in roles["rows"] if r["review_priority"] == "Review rotation first"]
    for role in concentrated:
        st.warning(f"{role['name']}: the leading player accounts for {role['top_share']:.1%} of role minutes. Review backup capability and availability before concluding recruitment is needed.")
    st.markdown("**Evidence still needed**")
    st.write("Actual roles and appearances → backup capability and availability → event-location and video review → assessment of tactical alternatives → recruitment roles and capability profiles.")
    st.download_button("Export Markdown report", to_markdown(report), "liverpool-audit.md", "text/markdown")
    st.download_button("Export full analysis as JSON", json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), "liverpool-audit.json", "application/json")

with source_tab:
    st.write(f"Input: {input_label}")
    st.markdown(f"[Match data source]({SOURCE_URL}) · [Field definitions](https://www.football-data.co.uk/notes.txt)")
    metadata_path = ROOT / "data/local/provenance.json"
    if uploaded is None and metadata_path.exists():
        st.json(json.loads(metadata_path.read_text(encoding="utf-8")))
    for limit in report["limits"]:
        st.write("• " + limit)
    st.caption("An independent learning project, not affiliated with Liverpool FC.")
