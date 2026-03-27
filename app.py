import streamlit as st
import csv
import os
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="NBA Under Analyzer", layout="centered")

TRACKER_FILE = "bet_tracker.csv"

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #0b1220 0%, #111827 100%);
        color: #f8fafc;
    }

    .block-container {
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    h1, h2, h3, h4, h5, h6, p, label, div, span {
        color: #f8fafc !important;
    }

    .main-wrap {
        background: rgba(17, 24, 39, 0.92);
        border: 1px solid #263041;
        border-radius: 18px;
        padding: 22px;
        margin-bottom: 18px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.30);
    }

    .author-text {
        color: #94a3b8 !important;
        margin-top: -8px;
        margin-bottom: 10px;
        font-size: 15px;
    }

    .subtle-text {
        color: #94a3b8 !important;
        font-size: 13px;
        margin-bottom: 8px;
    }

    .decision-pass {
        background: rgba(239, 68, 68, 0.14);
        border: 1px solid rgba(239, 68, 68, 0.45);
        border-radius: 14px;
        padding: 16px;
        font-size: 28px;
        font-weight: 800;
        text-align: center;
        color: #fecaca !important;
        margin-bottom: 12px;
    }

    .decision-safe {
        background: rgba(59, 130, 246, 0.14);
        border: 1px solid rgba(96, 165, 250, 0.45);
        border-radius: 14px;
        padding: 16px;
        font-size: 28px;
        font-weight: 800;
        text-align: center;
        color: #bfdbfe !important;
        margin-bottom: 12px;
    }

    .decision-execute {
        background: rgba(34, 197, 94, 0.14);
        border: 1px solid rgba(74, 222, 128, 0.45);
        border-radius: 14px;
        padding: 16px;
        font-size: 28px;
        font-weight: 800;
        text-align: center;
        color: #bbf7d0 !important;
        margin-bottom: 12px;
    }

    .risk-low {
        background: rgba(34, 197, 94, 0.12);
        border: 1px solid rgba(34, 197, 94, 0.35);
        border-radius: 12px;
        padding: 10px 12px;
        color: #86efac !important;
        font-weight: 700;
        margin-bottom: 14px;
    }

    .risk-medium {
        background: rgba(250, 204, 21, 0.12);
        border: 1px solid rgba(250, 204, 21, 0.35);
        border-radius: 12px;
        padding: 10px 12px;
        color: #fde68a !important;
        font-weight: 700;
        margin-bottom: 14px;
    }

    .risk-high {
        background: rgba(239, 68, 68, 0.12);
        border: 1px solid rgba(239, 68, 68, 0.35);
        border-radius: 12px;
        padding: 10px 12px;
        color: #fca5a5 !important;
        font-weight: 700;
        margin-bottom: 14px;
    }

    .metric-box {
        background: rgba(17, 24, 39, 0.92);
        border: 1px solid #2a3446;
        border-radius: 14px;
        padding: 14px;
        text-align: center;
        margin-bottom: 12px;
        min-height: 110px;
    }

    .metric-label {
        color: #94a3b8 !important;
        font-size: 14px;
        margin-bottom: 8px;
    }

    .metric-value {
        color: #f8fafc !important;
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.1;
    }

    .edge-box {
        background: rgba(30, 41, 59, 0.75);
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 14px;
        text-align: center;
        margin-bottom: 14px;
    }

    .edge-score {
        font-size: 2.4rem;
        font-weight: 900;
        color: #f8fafc !important;
    }

    .lock-pill {
        display: inline-block;
        padding: 10px 14px;
        border-radius: 999px;
        font-weight: 800;
        margin-bottom: 12px;
    }

    .lock-green {
        background: rgba(34, 197, 94, 0.16);
        border: 1px solid rgba(34, 197, 94, 0.45);
        color: #86efac !important;
    }

    .lock-blue {
        background: rgba(59, 130, 246, 0.16);
        border: 1px solid rgba(59, 130, 246, 0.45);
        color: #93c5fd !important;
    }

    .lock-red {
        background: rgba(239, 68, 68, 0.16);
        border: 1px solid rgba(239, 68, 68, 0.45);
        color: #fca5a5 !important;
    }

    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextInput"] input {
        background-color: #0f172a !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #0f172a !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }

    .stButton > button {
        width: 100%;
        border-radius: 12px;
        border: 1px solid #22c55e !important;
        background: linear-gradient(90deg, #15803d 0%, #22c55e 100%) !important;
        color: white !important;
        font-weight: 800 !important;
        padding: 0.8rem 1rem !important;
        box-shadow: 0 6px 18px rgba(34, 197, 94, 0.2);
    }

    .stButton > button:hover {
        background: linear-gradient(90deg, #166534 0%, #16a34a 100%) !important;
        color: white !important;
    }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #2563eb 0%, #60a5fa 100%) !important;
    }
</style>
""", unsafe_allow_html=True)


def initialize_tracker():
    if not os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "timestamp",
                "quarter",
                "time_left",
                "total_score",
                "lead",
                "line",
                "points_needed",
                "actual_pace",
                "pace_needed",
                "pace_ratio",
                "foul_risk",
                "decision",
                "lock_level",
                "edge_score",
                "probability",
                "bet_placed",
                "result"
            ])


def convert_time_to_minutes(time_str):
    minutes, seconds = time_str.split(":")
    return int(minutes) + int(seconds) / 60


def detect_foul_risk(lead, time_left):
    if lead <= 4 and time_left <= 4:
        return "EXTREME"
    elif lead <= 6 and time_left <= 3:
        return "HIGH"
    elif lead <= 8 and time_left <= 2:
        return "HIGH"
    elif lead <= 10 and time_left <= 1.5:
        return "MEDIUM"
    return "LOW"


def evaluate_game(total_score, lead, quarter, time_left, line, actual_pace, pace_needed, pace_ratio, foul_risk):
    if quarter != 4:
        return "PASS ❌"

    points_needed = line - total_score

    if foul_risk in ["EXTREME", "HIGH"]:
        return "PASS ❌"

    if lead < 10:
        return "PASS ❌"

    if points_needed <= 9 and time_left >= 5:
        return "PASS ❌"

    if actual_pace - pace_needed >= 2:
        return "PASS ❌"

    if lead >= 18 and time_left <= 5 and points_needed >= 12 and pace_ratio >= 1.15:
        return "EXECUTE BET ✅"

    if lead >= 15 and time_left <= 6 and points_needed >= 10 and pace_ratio >= 1.05:
        return "SAFE UNDER ✅"

    return "PASS ❌"


def estimate_probability(points_needed, time_left, lead, pace_needed, actual_pace, pace_ratio, foul_risk, decision):
    prob = 50

    if points_needed >= 20:
        prob += 20
    elif points_needed >= 15:
        prob += 12
    elif points_needed >= 10:
        prob += 6
    else:
        prob -= 15

    if time_left <= 3:
        prob += 15
    elif time_left <= 5:
        prob += 6

    if lead >= 15:
        prob += 6
    elif lead < 10:
        prob -= 10

    if pace_needed >= 3:
        prob += 10
    elif pace_needed <= 1.2:
        prob -= 10

    if actual_pace - pace_needed >= 1.5:
        prob -= 10

    if foul_risk == "HIGH":
        prob -= 20
    if foul_risk == "EXTREME":
        prob -= 30

    if decision == "PASS ❌":
        prob = min(prob, 60)
    elif decision == "SAFE UNDER ✅":
        prob = max(prob, 72)
        prob = min(prob, 84)
    elif decision == "EXECUTE BET ✅":
        prob = max(prob, 85)
        prob = min(prob, 95)

    return max(5, min(95, prob))


def get_lock_level(decision, prob):
    if "EXECUTE" in decision and prob >= 85:
        return "LOCK"
    elif "SAFE" in decision and prob >= 72:
        return "SAFE"
    return "PASS"


def get_edge_score(points_needed, time_left, lead, pace_ratio, foul_risk):
    score = 50

    if points_needed >= 20:
        score += 18
    elif points_needed >= 15:
        score += 12
    elif points_needed >= 10:
        score += 6
    else:
        score -= 12

    if time_left <= 3:
        score += 12
    elif time_left <= 5:
        score += 6

    if lead >= 18:
        score += 10
    elif lead >= 15:
        score += 6
    elif lead < 10:
        score -= 10

    if pace_ratio >= 1.15:
        score += 10
    elif pace_ratio >= 1.05:
        score += 5
    elif pace_ratio < 1.0:
        score -= 12

    if foul_risk == "LOW":
        score += 5
    elif foul_risk == "MEDIUM":
        score -= 5
    elif foul_risk == "HIGH":
        score -= 15
    elif foul_risk == "EXTREME":
        score -= 25

    return max(1, min(100, score))


initialize_tracker()

if "result_data" not in st.session_state:
    st.session_state.result_data = None

st.markdown('<div class="main-wrap">', unsafe_allow_html=True)
st.title("🏀 NBA Flow Analyzer")
st.markdown('<div class="author-text">Built by Charles Barnes</div>', unsafe_allow_html=True)
st.markdown('<div class="subtle-text">Live under decision tool with tracking, confidence, and edge scoring</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="main-wrap">', unsafe_allow_html=True)
st.subheader("Game Inputs")

quarter = st.selectbox("Quarter", [1, 2, 3, 4], index=3)
time_str = st.text_input("Time Left (M:SS)", "6:30")
total_score = st.number_input("Total Score (both teams)", value=228)
lead = st.number_input("Lead", value=10)
line = st.number_input("Live Betting Line", value=234.5)

analyze_clicked = st.button("Analyze Game", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

if analyze_clicked:
    time_left = convert_time_to_minutes(time_str)
    elapsed = ((quarter - 1) * 12) + (12 - time_left)

    points_needed = line - total_score
    pace_needed = points_needed / time_left if time_left > 0 else 0
    actual_pace = total_score / elapsed if elapsed > 0 else 0
    pace_ratio = pace_needed / actual_pace if actual_pace > 0 else 0

    foul_risk = detect_foul_risk(lead, time_left)
    decision = evaluate_game(
        total_score,
        lead,
        quarter,
        time_left,
        line,
        actual_pace,
        pace_needed,
        pace_ratio,
        foul_risk
    )
    prob = estimate_probability(
        points_needed,
        time_left,
        lead,
        pace_needed,
        actual_pace,
        pace_ratio,
        foul_risk,
        decision
    )
    lock_level = get_lock_level(decision, prob)
    edge_score = get_edge_score(points_needed, time_left, lead, pace_ratio, foul_risk)

    st.session_state.result_data = {
        "decision": decision,
        "prob": prob,
        "points_needed": points_needed,
        "time_left": time_left,
        "actual_pace": actual_pace,
        "pace_needed": pace_needed,
        "pace_ratio": pace_ratio,
        "foul_risk": foul_risk,
        "quarter": quarter,
        "time_str": time_str,
        "total_score": total_score,
        "lead": lead,
        "line": line,
        "lock_level": lock_level,
        "edge_score": edge_score
    }

if st.session_state.result_data:
    r = st.session_state.result_data

    st.markdown('<div class="main-wrap">', unsafe_allow_html=True)
    st.subheader("Final Decision")

    if r["lock_level"] == "LOCK":
        st.markdown('<div class="lock-pill lock-green">🔥 LOCK</div>', unsafe_allow_html=True)
    elif r["lock_level"] == "SAFE":
        st.markdown('<div class="lock-pill lock-blue">🔵 SAFE</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="lock-pill lock-red">❌ PASS</div>', unsafe_allow_html=True)

    if "EXECUTE" in r["decision"]:
        st.markdown(f'<div class="decision-execute">{r["decision"]} — {r["prob"]}%</div>', unsafe_allow_html=True)
    elif "SAFE" in r["decision"]:
        st.markdown(f'<div class="decision-safe">{r["decision"]} — {r["prob"]}%</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="decision-pass">{r["decision"]} — {r["prob"]}%</div>', unsafe_allow_html=True)

    st.markdown("### Confidence Meter")
    st.progress(r["prob"] / 100)
    st.markdown(f'<div class="subtle-text">Confidence Level: {r["prob"]}%</div>', unsafe_allow_html=True)

    st.markdown("### Edge Score")
    st.markdown(f'''
    <div class="edge-box">
        <div class="metric-label">Edge Score</div>
        <div class="edge-score">{r["edge_score"]}/100</div>
    </div>
    ''', unsafe_allow_html=True)

    if r["foul_risk"] == "LOW":
        st.markdown('<div class="risk-low">Foul Risk: LOW</div>', unsafe_allow_html=True)
    elif r["foul_risk"] == "MEDIUM":
        st.markdown('<div class="risk-medium">Foul Risk: MEDIUM</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="risk-high">Foul Risk: {r["foul_risk"]}</div>', unsafe_allow_html=True)

    st.subheader("Game Breakdown")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f'''
        <div class="metric-box">
            <div class="metric-label">Points Needed</div>
            <div class="metric-value">{r["points_needed"]:.1f}</div>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown(f'''
        <div class="metric-box">
            <div class="metric-label">Time Left</div>
            <div class="metric-value">{r["time_left"]:.2f}</div>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown(f'''
        <div class="metric-box">
            <div class="metric-label">Actual Pace</div>
            <div class="metric-value">{r["actual_pace"]:.2f}</div>
        </div>
        ''', unsafe_allow_html=True)

    with col2:
        st.markdown(f'''
        <div class="metric-box">
            <div class="metric-label">Needed Pace</div>
            <div class="metric-value">{r["pace_needed"]:.2f}</div>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown(f'''
        <div class="metric-box">
            <div class="metric-label">Pace Ratio</div>
            <div class="metric-value">{r["pace_ratio"]:.2f}</div>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown(f'''
        <div class="metric-box">
            <div class="metric-label">Lead</div>
            <div class="metric-value">{r["lead"]}</div>
        </div>
        ''', unsafe_allow_html=True)

    st.subheader("Save This Check")
    bet_placed = st.selectbox("Did you place this bet?", ["n", "y"])
    result = st.selectbox("Result", ["pending", "win", "loss", "push"])

    if st.button("Save to Tracker", use_container_width=True):
        with open(TRACKER_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now(),
                r["quarter"],
                r["time_str"],
                r["total_score"],
                r["lead"],
                r["line"],
                round(r["points_needed"], 1),
                round(r["actual_pace"], 2),
                round(r["pace_needed"], 2),
                round(r["pace_ratio"], 2),
                r["foul_risk"],
                r["decision"],
                r["lock_level"],
                r["edge_score"],
                r["prob"],
                bet_placed,
                result
            ])
        st.success("Saved to tracker!")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="main-wrap">', unsafe_allow_html=True)
st.subheader("Tracker Dashboard")

if os.path.exists(TRACKER_FILE):
    df = pd.read_csv(TRACKER_FILE)

    if not df.empty:
        st.write("Recent Entries")
        st.dataframe(df.tail(10), use_container_width=True)

        placed_df = df[df["bet_placed"] == "y"]
        win_df = placed_df[placed_df["result"] == "win"]
        total_bets = len(placed_df)
        wins = len(win_df)

        if total_bets > 0:
            win_rate = (wins / total_bets) * 100
            st.write(f"Win Rate: {win_rate:.1f}%")
        else:
            st.write("No bets placed yet.")

st.markdown('</div>', unsafe_allow_html=True)
st.caption("© 2026 Charles Barnes — NBA Flow Analyzer")
