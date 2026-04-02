import streamlit as st
import pandas as pd
import time
import re
from datetime import datetime

st.set_page_config(page_title="NBA Flow Analyzer", layout="wide")

st.title("🏀 NBA Flow Analyzer")
st.caption("Live bet analyzer + tracker")

# ---------------------------
# Session state setup
# ---------------------------
if "bet_history" not in st.session_state:
    st.session_state.bet_history = []

if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = {}

# ---------------------------
# Helper functions
# ---------------------------
def parse_bet_line_from_name(bet_name, fallback_line):
    match = re.search(r"(\d+(\.\d+)?)", bet_name)
    if match:
        return float(match.group(1))
    return float(fallback_line)


def american_to_implied_probability(odds):
    if odds < 0:
        return round((abs(odds) / (abs(odds) + 100)) * 100, 1)
    return round((100 / (odds + 100)) * 100, 1)


def get_cushion_label(cushion_score):
    if cushion_score >= 34:
        return "Elite"
    if cushion_score >= 28:
        return "Strong"
    if cushion_score >= 22:
        return "Decent"
    if cushion_score >= 16:
        return "Thin"
    if cushion_score > 0:
        return "Danger"
    return "Auto-Pass"


def get_q4_heat_label(q1_total, q2_total, q3_total, q4_current):
    previous_quarters = [q1_total, q2_total, q3_total]
    avg_previous = sum(previous_quarters) / 3

    if q4_current >= avg_previous + 8:
        return "HOT"
    if q4_current <= avg_previous - 8:
        return "COOL"
    return "NEUTRAL"


def get_q4_pace_projection(q4_current, time_left):
    minutes_elapsed = 12 - time_left

    if minutes_elapsed <= 0:
        return float(q4_current)

    pace_per_minute = q4_current / minutes_elapsed
    projected_full_q4 = pace_per_minute * 12
    return round(projected_full_q4, 1)


def get_required_cushion_gates(time_left):
    """
    Time-adjusted cushion system:
    more time left = need more cushion
    """
    if time_left > 6.0:
        return {"smart": 30, "cruise": 34}
    elif time_left > 5.0:
        return {"smart": 28, "cruise": 32}
    elif time_left > 4.0:
        return {"smart": 25, "cruise": 29}
    else:
        return {"smart": 22, "cruise": 26}


def get_bet_size_label(verdict):
    if verdict == "CRUISE CONTROL ✅":
        return "FULL BET 💰"
    if verdict == "SMART ACTION 🎯":
        return "SMALL BET 🎯"
    return "NO BET 🚫"


def apply_probability_caps(probability, quarter, time_left, lead, cushion_score, q4_heat, q4_projected):
    probability = min(probability, 92)

    if quarter == "4Q":
        probability = min(probability, 88)

        if time_left <= 6.0:
            probability = min(probability, 85)

        if lead < 15:
            probability = min(probability, 82)

        if cushion_score < 25:
            probability = min(probability, 80)

        if cushion_score < 22:
            probability = min(probability, 76)

        if q4_heat == "HOT":
            probability = min(probability, 72)

        if q4_projected >= 48:
            probability = min(probability, 72)
        elif q4_projected >= 42:
            probability = min(probability, 76)
        elif q4_projected >= 36:
            probability = min(probability, 80)

        if lead < 10 and time_left <= 4.0:
            probability = min(probability, 68)

        if lead >= 18 and cushion_score >= 30 and q4_heat == "COOL" and q4_projected <= 34:
            probability = min(probability, 86)

    return max(1, min(int(round(probability)), 99))


def is_bet_allowed(verdict):
    return verdict in ["CRUISE CONTROL ✅", "SMART ACTION 🎯"]


def calculate_analysis(
    team_1,
    team_2,
    bet_name,
    quarter,
    time_left,
    lead,
    current_total,
    bet_line,
    odds,
    q1_total,
    q2_total,
    q3_total,
    q4_current
):
    probability = 50
    notes = []

    parsed_line = parse_bet_line_from_name(bet_name, bet_line)
    implied_probability = american_to_implied_probability(odds)
    cushion_score = round(parsed_line - current_total, 1)
    cushion_label = get_cushion_label(cushion_score)
    q4_heat = get_q4_heat_label(q1_total, q2_total, q3_total, q4_current)
    q4_projected = get_q4_pace_projection(q4_current, time_left)
    ppm_required = round(cushion_score / time_left, 2) if time_left > 0 else 0
    cushion_gates = get_required_cushion_gates(time_left)
    smart_cushion_gate = cushion_gates["smart"]
    cruise_cushion_gate = cushion_gates["cruise"]

    verdict = "PASS ❌"
    stability = "Unstable"

    trap_flag = False
    pass_flag = False

    notes.append(f"Time-adjusted cushion gate → Smart: {smart_cushion_gate} | Cruise: {cruise_cushion_gate}")
    notes.append(f"Required pace to lose: {ppm_required} pts/min")

    # ---------------------------
    # Quarter timing
    # ---------------------------
    if quarter == "4Q":
        probability += 10
        notes.append("4Q timing boost")
    elif quarter == "3Q":
        probability += 2
        notes.append("3Q has some value, but less certainty than 4Q")
    else:
        probability -= 10
        notes.append("Early quarter = too much time for variance")

    # ---------------------------
    # Lead logic
    # ---------------------------
    if lead >= 22:
        probability += 20
        notes.append("Massive blowout script favors slower finish")
    elif lead >= 18:
        probability += 16
        notes.append("Strong blowout script favors slower finish")
    elif lead >= 16:
        probability += 13
        notes.append("Strong lead supports under")
    elif lead >= 12:
        probability += 9
        notes.append("Decent lead supports under")
    elif lead >= 10:
        probability += 4
        notes.append("Minimum acceptable lead")
    elif lead >= 8:
        probability -= 4
        trap_flag = True
        notes.append("Borderline lead")
    else:
        probability -= 12
        pass_flag = True
        notes.append("Close game raises foul/comeback risk")

    # ---------------------------
    # Time-left logic
    # ---------------------------
    if time_left <= 2.0:
        probability += 12
        notes.append("Very late-game clock advantage")
    elif time_left <= 3.0:
        probability += 9
        notes.append("Strong late-game clock advantage")
    elif time_left <= 4.5:
        probability += 6
        notes.append("Good late-game window")
    elif time_left <= 6.0:
        probability += 3
        notes.append("Usable late-game window")
    elif time_left <= 7.0:
        probability += 1
        notes.append("Early late-game window")
    else:
        probability -= 4
        pass_flag = True
        notes.append("Too much time left for comfort")

    # ---------------------------
    # Cushion logic
    # ---------------------------
    if cushion_score >= 34:
        probability += 18
        notes.append("Elite cushion score")
    elif cushion_score >= 30:
        probability += 14
        notes.append("Strong cushion score")
    elif cushion_score >= 25:
        probability += 10
        notes.append("Good cushion score")
    elif cushion_score >= 22:
        probability += 5
        notes.append("Acceptable cushion score")
    elif cushion_score >= 16:
        probability -= 6
        trap_flag = True
        notes.append("Thin cushion: still vulnerable to a run")
    elif cushion_score >= 10:
        probability -= 12
        trap_flag = True
        notes.append("Danger cushion: too thin for comfort")
    else:
        probability -= 24
        pass_flag = True
        notes.append("Not enough cushion")

    # ---------------------------
    # Time-adjusted cushion gate
    # ---------------------------
    if cushion_score < smart_cushion_gate:
        probability -= 8
        trap_flag = True
        notes.append("Below Smart Action cushion threshold")
    else:
        probability += 4
        notes.append("Passed Smart Action cushion threshold")

    if cushion_score >= cruise_cushion_gate:
        probability += 4
        notes.append("Passed Cruise cushion threshold")

    # ---------------------------
    # Close-game kill switch
    # ---------------------------
    if quarter == "4Q" and time_left <= 3.0 and lead < 8:
        probability -= 22
        pass_flag = True
        notes.append("Auto-pass: too close too late")
    elif quarter == "4Q" and time_left <= 4.0 and lead < 10:
        probability -= 10
        trap_flag = True
        notes.append("Late competitive game = foul/comeback danger")
    elif quarter == "4Q" and time_left <= 5.0 and lead < 12:
        probability -= 6
        trap_flag = True
        notes.append("Lead not strong enough for this time window")

    # ---------------------------
    # Blowout / dead-game bonus
    # ---------------------------
    if quarter == "4Q" and time_left <= 5.0 and lead >= 18:
        probability += 8
        notes.append("Dead-game bonus: lower foul urgency")
    elif quarter == "4Q" and time_left <= 4.0 and lead >= 15:
        probability += 5
        notes.append("Blowout stability boost")

    # ---------------------------
    # Q4 heat / cooling logic
    # ---------------------------
    if q4_heat == "HOT":
        probability -= 12
        trap_flag = True
        notes.append("Q4 is running hot vs earlier quarters")
    elif q4_heat == "COOL":
        probability += 6
        notes.append("Q4 scoring is cooling off")
    else:
        notes.append("Q4 flow is neutral")

    # ---------------------------
    # Q4 pace projection logic
    # ---------------------------
    if q4_projected >= 48:
        probability -= 18
        trap_flag = True
        notes.append("Q4 pace projecting extremely high scoring finish")
    elif q4_projected >= 42:
        probability -= 12
        trap_flag = True
        notes.append("Q4 pace projecting high scoring finish")
    elif q4_projected >= 36:
        probability -= 6
        notes.append("Q4 pace slightly elevated")
    elif q4_projected <= 28 and quarter == "4Q":
        probability += 4
        notes.append("Q4 pace projecting slow finish")

    # ---------------------------
    # Extra raw Q4 scoring warning
    # ---------------------------
    if q4_current >= 35:
        probability -= 8
        trap_flag = True
        notes.append("Q4 current points already elevated")
    elif q4_current <= 24 and quarter == "4Q":
        probability += 4
        notes.append("Q4 scoring pace is controlled")

    # ---------------------------
    # Scoring pace pressure near line
    # ---------------------------
    if current_total >= parsed_line - 6:
        probability -= 8
        trap_flag = True
        notes.append("Current total is already pressing the line")
    elif current_total <= parsed_line - 15:
        probability += 4
        notes.append("Current total still has breathing room")

    # ---------------------------
    # Odds gate
    # ---------------------------
    if -400 <= odds <= -280:
        probability += 3
        notes.append("Odds fit your preferred NBA gate")
    else:
        probability -= 4
        notes.append("Odds outside preferred NBA gate")

    # ---------------------------
    # Late volatility buffer
    # ---------------------------
    if quarter == "4Q" and time_left <= 6.0:
        probability -= 4
        notes.append("Late volatility buffer applied")

    probability = max(1, min(int(round(probability)), 99))

    # ---------------------------
    # Confidence caps
    # ---------------------------
    uncapped_probability = probability
    probability = apply_probability_caps(
        probability=probability,
        quarter=quarter,
        time_left=time_left,
        lead=lead,
        cushion_score=cushion_score,
        q4_heat=q4_heat,
        q4_projected=q4_projected
    )

    if probability < uncapped_probability:
        notes.append(f"Confidence cap applied: {uncapped_probability}% → {probability}%")

    # ---------------------------
    # Final verdict
    # ---------------------------
    if pass_flag:
        verdict = "PASS ❌"
        stability = "Unstable"
    elif (
        probability >= 78
        and lead >= 16
        and cushion_score >= cruise_cushion_gate
        and q4_heat != "HOT"
        and q4_projected < 36
        and ppm_required >= 5.3
    ):
        verdict = "CRUISE CONTROL ✅"
        stability = "Stable"
    elif (
        probability >= 70
        and lead >= 12
        and cushion_score >= smart_cushion_gate
        and q4_heat != "HOT"
        and q4_projected < 42
        and ppm_required >= 4.9
    ):
        verdict = "SMART ACTION 🎯"
        stability = "Medium"
    else:
        verdict = "PASS ❌"
        stability = "Unstable"

    bet_size_label = get_bet_size_label(verdict)
    locked_bet_allowed = is_bet_allowed(verdict)

    if verdict == "CRUISE CONTROL ✅":
        locked_decision = "BET THIS ✅"
        notes.append("Locked Mode: cruise setup approved")
    elif verdict == "SMART ACTION 🎯":
        locked_decision = "SMALL ACTION ONLY 🎯"
        notes.append("Locked Mode: Smart Action approved for smaller sizing")
    else:
        locked_decision = "NO PLAY ❌"
        notes.append("Locked Mode: setup blocked")

    return {
        "probability": probability,
        "implied_probability": implied_probability,
        "verdict": verdict,
        "locked_decision": locked_decision,
        "locked_bet_allowed": locked_bet_allowed,
        "stability": stability,
        "notes": notes,
        "cushion_score": cushion_score,
        "cushion_label": cushion_label,
        "parsed_bet_line": parsed_line,
        "q4_heat": q4_heat,
        "q4_projected": q4_projected,
        "ppm_required": ppm_required,
        "smart_cushion_gate": smart_cushion_gate,
        "cruise_cushion_gate": cruise_cushion_gate,
        "bet_size_label": bet_size_label,
    }

# ---------------------------
# Input section
# ---------------------------
st.subheader("Game Input")

col1, col2 = st.columns(2)

with col1:
    team_1 = st.text_input("Team 1", value="SAC Kings")
    team_2 = st.text_input("Team 2", value="BKN Nets")
    bet_name = st.text_input("Bet Name", value="Under 216.5")
    odds = st.number_input("Odds", value=-300, step=1)

with col2:
    quarter = st.selectbox("Quarter", ["1Q", "2Q", "3Q", "4Q"], index=3)
    time_left = st.number_input("Time Left (minutes)", min_value=0.0, max_value=12.0, value=6.2, step=0.1)
    lead = st.number_input("Lead Margin", min_value=0, max_value=60, value=19, step=1)
    current_total = st.number_input("Current Total Points", min_value=0, max_value=300, value=185, step=1)
    bet_line = st.number_input("Bet Line", min_value=0.0, max_value=350.0, value=216.5, step=0.5)

st.markdown("### Quarter Flow Inputs")
flow_col1, flow_col2, flow_col3, flow_col4 = st.columns(4)

with flow_col1:
    q1_total = st.number_input("Q1 Total", min_value=0, max_value=100, value=54, step=1)

with flow_col2:
    q2_total = st.number_input("Q2 Total", min_value=0, max_value=100, value=50, step=1)

with flow_col3:
    q3_total = st.number_input("Q3 Total", min_value=0, max_value=100, value=47, step=1)

with flow_col4:
    q4_current = st.number_input("Q4 Current Points", min_value=0, max_value=100, value=22, step=1)

# ---------------------------
# Analyze button with visual feedback
# ---------------------------
st.markdown("---")

if st.button("Analyze Bet", use_container_width=True):
    progress_bar = st.progress(0)
    status_text = st.empty()

    steps = [
        "Loading game state...",
        "Checking score margin...",
        "Checking quarter + time left...",
        "Measuring foul risk...",
        "Reading quarter-by-quarter flow...",
        "Projecting Q4 pace...",
        "Calculating cushion score...",
        "Applying confidence
