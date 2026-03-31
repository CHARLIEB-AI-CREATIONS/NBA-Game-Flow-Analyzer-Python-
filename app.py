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
    if cushion_score >= 8:
        return "Good"
    if cushion_score >= 5:
        return "Playable"
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


def apply_probability_caps(probability, quarter, time_left, lead, cushion_score, q4_heat):
    """
    Live betting should never show fake certainty.
    This keeps probabilities realistic.
    """
    # Global hard cap for live betting
    probability = min(probability, 92)

    if quarter == "4Q":
        probability = min(probability, 88)

        # Late-game volatility still exists even in great spots
        if time_left <= 6.0:
            probability = min(probability, 85)

        # Extra cap for not-quite-dead games
        if lead < 15:
            probability = min(probability, 82)

        # Thin cushion should never read elite
        if cushion_score < 8:
            probability = min(probability, 78)

        # Hot Q4 should never read high confidence
        if q4_heat == "HOT":
            probability = min(probability, 72)

        # Close enough to still foul/swing
        if lead < 10 and time_left <= 4.0:
            probability = min(probability, 68)

        # Best-case elite setup can stay strong, but not absurd
        if lead >= 15 and cushion_score >= 12 and q4_heat == "COOL" and time_left <= 6.0:
            probability = min(probability, 86)

    return max(1, min(int(round(probability)), 99))


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

    verdict = "PASS ❌"
    stability = "Unstable"

    trap_flag = False
    pass_flag = False

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
    if lead >= 20:
        probability += 20
        notes.append("Massive blowout script favors slower finish")
    elif lead >= 15:
        probability += 16
        notes.append("Blowout script favors slower finish")
    elif lead >= 12:
        probability += 11
        notes.append("Strong lead supports under")
    elif lead >= 10:
        probability += 8
        notes.append("Solid lead supports under")
    elif lead >= 8:
        probability += 2
        notes.append("Borderline lead")
    elif lead >= 6:
        probability -= 4
        notes.append("Lead is not strong enough for comfort")
    else:
        probability -= 12
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
    elif time_left <= 5.0:
        probability += 5
        notes.append("Good live window")
    elif time_left <= 7.0:
        probability += 2
        notes.append("Playable live window")
    else:
        probability -= 4
        notes.append("Too much time left for comfort")

    # ---------------------------
    # Cushion logic
    # ---------------------------
    if cushion_score >= 15:
        probability += 16
        notes.append("Elite cushion score")
    elif cushion_score >= 10:
        probability += 10
        notes.append("Strong cushion score")
    elif cushion_score >= 8:
        probability += 7
        notes.append("Good cushion score")
    elif cushion_score >= 5:
        probability += 2
        notes.append("Playable cushion score")
    elif cushion_score >= 3:
        probability -= 8
        trap_flag = True
        notes.append("Thin cushion: one run can kill this")
    elif cushion_score >= 1:
        probability -= 16
        trap_flag = True
        notes.append("Danger cushion: fake-safe profile")
    else:
        probability -= 30
        pass_flag = True
        notes.append("No cushion: auto-pass zone")

    # ---------------------------
    # One-possession danger
    # ---------------------------
    if cushion_score <= 3:
        probability -= 10
        trap_flag = True
        notes.append("One-possession loss risk elevated")

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

    # ---------------------------
    # Blowout / dead-game bonus
    # ---------------------------
    if quarter == "4Q" and time_left <= 4.0 and lead >= 15:
        probability += 8
        notes.append("Dead-game bonus: lower foul urgency")
    elif quarter == "4Q" and time_left <= 3.0 and lead >= 12:
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

    # Extra raw Q4 scoring warning
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
    if current_total >= parsed_line - 2:
        probability -= 8
        trap_flag = True
        notes.append("Current total is already pressing the line")
    elif current_total <= parsed_line - 10:
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
        probability -= 5
        notes.append("Late volatility buffer applied")

    # Clamp before cap system
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
        q4_heat=q4_heat
    )

    if probability < uncapped_probability:
        notes.append(f"Confidence cap applied: {uncapped_probability}% → {probability}%")

    # ---------------------------
    # Final verdict
    # ---------------------------
    if pass_flag:
        verdict = "PASS ❌"
        stability = "Unstable"
    elif trap_flag and probability < 72:
        verdict = "TRAP 🚨"
        stability = "Unstable"
    elif probability >= 82 and cushion_score >= 8 and q4_heat != "HOT" and lead >= 12:
        verdict = "CRUISE CONTROL ✅"
        stability = "Stable"
    elif probability >= 72 and cushion_score >= 5 and not pass_flag:
        verdict = "PLAYABLE ⚠️"
        stability = "Medium"
    elif trap_flag:
        verdict = "TRAP 🚨"
        stability = "Unstable"
    else:
        verdict = "PASS ❌"
        stability = "Unstable"

    return {
        "probability": probability,
        "implied_probability": implied_probability,
        "verdict": verdict,
        "stability": stability,
        "notes": notes,
        "cushion_score": cushion_score,
        "cushion_label": cushion_label,
        "parsed_bet_line": parsed_line,
        "q4_heat": q4_heat,
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
        "Calculating cushion score...",
        "Applying confidence caps...",
        "Finalizing probability...",
    ]

    for i in range(100):
        time.sleep(0.02)
        progress_bar.progress(i + 1)

        if i < 12:
            status_text.text(steps[0])
        elif i < 25:
            status_text.text(steps[1])
        elif i < 40:
            status_text.text(steps[2])
        elif i < 55:
            status_text.text(steps[3])
        elif i < 70:
            status_text.text(steps[4])
        elif i < 82:
            status_text.text(steps[5])
        elif i < 92:
            status_text.text(steps[6])
        else:
            status_text.text(steps[7])

    result = calculate_analysis(
        team_1=team_1,
        team_2=team_2,
        bet_name=bet_name,
        quarter=quarter,
        time_left=time_left,
        lead=lead,
        current_total=current_total,
        bet_line=bet_line,
        odds=odds,
        q1_total=q1_total,
        q2_total=q2_total,
        q3_total=q3_total,
        q4_current=q4_current,
    )

    st.session_state.analysis_done = True
    st.session_state.analysis_result = result

    status_text.text("Analysis Complete ✅")

# ---------------------------
# Analysis output
# ---------------------------
if st.session_state.analysis_done:
    st.subheader("Analysis Result")

    result = st.session_state.analysis_result

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Probability", f"{result['probability']}%")

    with c2:
        st.metric("Implied Prob", f"{result['implied_probability']}%")

    with c3:
        st.metric("Stability", result["stability"])

    with c4:
        st.metric("Verdict", result["verdict"])

    d1, d2, d3 = st.columns(3)

    with d1:
        st.metric("Cushion Score", result["cushion_score"])

    with d2:
        st.metric("Cushion Label", result["cushion_label"])

    with d3:
        st.metric("Q4 Heat", result["q4_heat"])

    st.write(f"**Matchup:** {team_1} vs {team_2}")
    st.write(f"**Bet:** {bet_name}")
    st.write(f"**Quarter:** {quarter}")
    st.write(f"**Time Left:** {time_left}")
    st.write(f"**Lead Margin:** {lead}")
    st.write(f"**Current Total:** {current_total}")
    st.write(f"**Bet Line:** {bet_line}")
    st.write(f"**Parsed Bet Line:** {result['parsed_bet_line']}")
    st.write(f"**Odds:** {odds}")
    st.write(f"**Q1 / Q2 / Q3 / Q4 Current:** {q1_total} / {q2_total} / {q3_total} / {q4_current}")

    st.markdown("**Why:**")
    for note in result["notes"]:
        st.write(f"- {note}")

    st.markdown("---")

    if st.button("Save Bet to Tracker", use_container_width=True):
        st.session_state.bet_history.append({
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Team 1": team_1,
            "Team 2": team_2,
            "Bet Name": bet_name,
            "Quarter": quarter,
            "Time Left": time_left,
            "Lead": lead,
            "Current Total": current_total,
            "Bet Line": bet_line,
            "Parsed Bet Line": result["parsed_bet_line"],
            "Odds": odds,
            "Q1 Total": q1_total,
            "Q2 Total": q2_total,
            "Q3 Total": q3_total,
            "Q4 Current": q4_current,
            "Probability": f"{result['probability']}%",
            "Implied Prob": f"{result['implied_probability']}%",
            "Cushion Score": result["cushion_score"],
            "Cushion Label": result["cushion_label"],
            "Q4 Heat": result["q4_heat"],
            "Stability": result["stability"],
            "Verdict": result["verdict"],
            "Status": "Pending",
        })
        st.success("Bet saved to tracker ✅")

# ---------------------------
# Tracker section
# ---------------------------
st.markdown("---")
st.subheader("Bet Tracker")

if len(st.session_state.bet_history) == 0:
    st.info("No bets saved yet.")
else:
    tracker_df = pd.DataFrame(st.session_state.bet_history)

    for i in range(len(tracker_df)):
        st.markdown(f"### Bet #{i + 1}")
        col_a, col_b = st.columns([3, 1])

        with col_a:
            st.write(f"**Time:** {tracker_df.loc[i, 'Time']}")
            st.write(f"**Game:** {tracker_df.loc[i, 'Team 1']} vs {tracker_df.loc[i, 'Team 2']}")
            st.write(f"**Bet:** {tracker_df.loc[i, 'Bet Name']}")
            st.write(f"**Odds:** {tracker_df.loc[i, 'Odds']}")
            st.write(f"**Probability:** {tracker_df.loc[i, 'Probability']}")
            st.write(f"**Implied Prob:** {tracker_df.loc[i, 'Implied Prob']}")
            st.write(f"**Cushion Score:** {tracker_df.loc[i, 'Cushion Score']}")
            st.write(f"**Cushion Label:** {tracker_df.loc[i, 'Cushion Label']}")
            st.write(f"**Q4 Heat:** {tracker_df.loc[i, 'Q4 Heat']}")
            st.write(f"**Stability:** {tracker_df.loc[i, 'Stability']}")
            st.write(f"**Verdict:** {tracker_df.loc[i, 'Verdict']}")

        with col_b:
            new_status = st.selectbox(
                f"Status for Bet #{i + 1}",
                ["Pending", "Win", "Loss", "Pass"],
                index=["Pending", "Win", "Loss", "Pass"].index(tracker_df.loc[i, "Status"]),
                key=f"status_{i}"
            )
            st.session_state.bet_history[i]["Status"] = new_status

        st.markdown("---")

    final_df = pd.DataFrame(st.session_state.bet_history)
    st.dataframe(final_df, use_container_width=True)

    csv = final_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Tracker CSV",
        data=csv,
        file_name="nba_bet_tracker.csv",
        mime="text/csv",
        use_container_width=True
    )
