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
    st.markdown("### LIVERPOOL\nSquad Audit / 阵容诊断")
    st.caption("2026–27 · 第一阶段")
    st.write(f"固定截止日期：{DEFAULT_AS_OF}")
    window = st.selectbox("比赛范围", ["赛季至今", "最近 8 场", "最近 5 场"])
    venue_name = st.selectbox("主客场", ["全部", "主场", "客场"])
    exclude_red = st.checkbox("排除任一方有红牌的整场比赛", value=False)
    st.divider()
    st.caption("可使用本地下载文件，或上传相同格式的数据。")
    uploaded = st.file_uploader("比赛 CSV（Football-Data E0 格式）", type=["csv"])
    lineup = st.file_uploader("球员出场 CSV（可选）", type=["csv"])
    st.download_button("下载出场数据模板", (ROOT / "data/templates/appearances.csv").read_bytes(), "appearances.csv", "text/csv")

st.caption("FOOTBALL INTELLIGENCE / 01")
st.title("利物浦，哪里需要补强？")
st.write("从比赛表现与位置覆盖建立证据，再判断补强方向。")
st.caption("本版仅分析英超；位置级建议需要完整出场和阵容证据。")

try:
    if uploaded is not None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "uploaded.csv"
            path.write_bytes(uploaded.getvalue())
            records = read_matches(path)
        input_label = "用户上传 CSV（内容未独立核实）"
    else:
        path = ROOT / "data/local/E0-2627.csv"
        if not path.exists():
            st.info("尚未下载比赛数据。在项目目录运行下面的命令，再刷新本页。")
            st.code("python scripts/fetch_data.py", language="bash")
            st.markdown(f"也可[手动下载比赛 CSV]({SOURCE_URL})，然后在左侧上传。")
            st.stop()
        records = read_matches(path)
        input_label = "本地 Football-Data.co.uk 快照"
    appearances = read_appearances(lineup.getvalue().decode("utf-8-sig"), records) if lineup else []
    report = analyze(records, exclude_red=exclude_red,
                     venue={"全部": "ALL", "主场": "H", "客场": "A"}[venue_name],
                     last_n={"赛季至今": None, "最近 8 场": 8, "最近 5 场": 5}[window],
                     appearances=appearances)
except (OSError, UnicodeError, ValueError) as exc:
    st.error(f"数据未通过检查：{exc}")
    st.stop()

report["input_label"] = input_label
report["input_sha256"] = hashlib.sha256(uploaded.getvalue() if uploaded is not None else path.read_bytes()).hexdigest()
s, b = report["summary"], report["benchmark"]
columns = st.columns(4)
columns[0].metric("已分析比赛", s["matches"], f"{s['wins']} 胜 · {s['draws']} 平 · {s['losses']} 负", delta_color="off")
columns[1].metric("积分", fmt(s["points_total"], 0))
columns[2].metric("场均 xG · 创造机会", fmt(s["xg_for_per_match"]))
columns[3].metric("场均 xGA · 对手机会", fmt(s["xg_against_per_match"]))
if s["matches"] < 8:
    st.warning("当前筛选少于 8 场：仅展示统计，暂停触发补强相关规则。")

matches_tab, squad_tab, diagnosis_tab, source_tab = st.tabs(["比赛表现", "阵容覆盖", "诊断与证据", "数据与方法"])
with matches_tab:
    st.subheader("机会创造与防守风险")
    st.caption("xG 为预期进球，xGA 为对手预期进球。它们描述射门机会，不是预期比分。")
    if report["matches"]:
        frame = pd.DataFrame(report["matches"])
        trend = frame.set_index("date")[["xg_for", "xg_against"]].rename(columns={"xg_for": "利物浦 xG", "xg_against": "对手 xG"})
        st.line_chart(trend, color=["#c8102e", "#177e72"])
        evidence = frame[["date", "match_id", "opponent", "venue", "goals_for", "goals_against", "xg_for", "xg_against", "shots_for", "shots_against", "red_card_match"]]
        st.dataframe(evidence.rename(columns={"date": "日期", "opponent": "对手", "venue": "主客场", "goals_for": "进球", "goals_against": "失球", "xg_for": "xG", "xg_against": "xGA", "shots_for": "射门", "shots_against": "对手射门", "red_card_match": "出现红牌"}), hide_index=True)
        st.download_button("下载比赛标识（用于填写出场数据）", frame[["match_id", "date", "opponent", "venue"]].to_csv(index=False), "match_ids.csv", "text/csv")
    else:
        st.info("当前筛选没有比赛。")
    st.subheader("同期联赛参照")
    comparison = []
    for key, label in (("goals_for", "场均进球"), ("goals_against", "场均失球"), ("xg_for", "场均 xG"), ("xg_against", "场均 xGA"), ("shots_for", "场均射门")):
        comparison.append({"指标": label, "利物浦": s[key + "_per_match"], "其他球队": b[key + "_per_match"], "有效比赛数": s[key + "_n"]})
    st.dataframe(pd.DataFrame(comparison), hide_index=True)
    st.caption("比较范围与筛选条件一致；未调整对手强弱。缺失值为空，不会被当成 0。")

with squad_tab:
    roles = report["roles"]
    st.subheader("位置覆盖与轮换集中度")
    st.write(f"完整出场记录：{roles['complete_matches']} / {roles['eligible_matches']} 场双方无红牌比赛。")
    if not appearances:
        st.info("尚无真实球员出场数据。请下载模板，录入球员在每场比赛实际位置上的分钟数和来源，再上传。")
    st.caption("同一球员换位置时拆分分钟；未出场的替补能力无法从这张表推断。红牌比赛暂不参与完整性判断。")
    rows = [{"位置": r["name"], "已用人数": r["players_used"] if r["minutes"] else None,
             "位置出现的完整比赛": r["role_matches"], "最常使用球员": r["most_used"],
             "主力分钟占比": r["top_share"], "核查优先级": r["review_priority"]} for r in roles["rows"]]
    st.dataframe(pd.DataFrame(rows), hide_index=True)
    with st.expander("如何准备出场数据"):
        st.write("先从比赛表现页下载 match_id，再按模板逐行录入。分钟使用 0–90 的常规时间口径；不包含补时。每位球员同场各位置分钟之和不能超过 90。")
        st.write("系统仅把 990 个球队分钟的无红牌比赛视为完整。至少 8 场完整数据、覆盖所选无红牌比赛的 80%，才检查轮换集中。位置主力分钟占比达到 85% 时提示复核。")
        st.write("中后卫等多人共同承担的位置，分钟占比按该位置总分钟计算，不代表阵型人数或替补储备。")

with diagnosis_tab:
    st.subheader("证据链，而非一句转会结论")
    for signal in report["signals"]:
        with st.container(border=True):
            st.markdown(f"**{signal['title']}**")
            st.write(f"本队 {fmt(signal['actual'])} / 同期参照 {fmt(signal['benchmark'])}。触发条件：{signal['rule']}。")
            st.write(signal["interpretation"])
            st.caption(signal["status"])
    if not report["signals"]:
        st.info("当前没有触发比赛线索规则，或有效样本不足。不能据此认定阵容没有缺陷。")
    concentrated = [r for r in roles["rows"] if r["review_priority"] == "优先核查轮换"]
    for role in concentrated:
        st.warning(f"{role['name']}：主力承担 {role['top_share']:.1%} 的该位置分钟。应核查替补水平与可用性；尚不能认定需要引援。")
    st.markdown("**下一步需要补齐的证据**")
    st.write("球员实际角色与出场 → 替补和伤停情况 → 事件区域及录像复核 → 排除可通过战术调整解决的问题 → 再确定补强位置和能力画像。")
    st.download_button("导出诊断报告 Markdown", to_markdown(report), "liverpool-audit.md", "text/markdown")
    st.download_button("导出完整分析 JSON", json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), "liverpool-audit.json", "application/json")

with source_tab:
    st.write(f"输入：{input_label}")
    st.markdown(f"[比赛数据来源]({SOURCE_URL}) · [字段说明](https://www.football-data.co.uk/notes.txt)")
    metadata_path = ROOT / "data/local/provenance.json"
    if uploaded is None and metadata_path.exists():
        st.json(json.loads(metadata_path.read_text(encoding="utf-8")))
    for limit in report["limits"]:
        st.write("• " + limit)
    st.caption("本项目为独立学习项目，与利物浦俱乐部无隶属关系。")
