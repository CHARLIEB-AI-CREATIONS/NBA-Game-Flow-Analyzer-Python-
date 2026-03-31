import streamlit as st
import pandas as pd
import time
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
def calculate_analysis(team_1, team_2, bet_name, quarter, time_left, lead, current_total, bet_line, odds):
    """
    Basic placeholder logic.
    You can tighten this later with your real system.
    """
    probability = 50
    verdict = "PASS"
    stability = "Unstable"
    notes = []

    # Quarter boost
    if quarter == "4Q":
        probability += 10
        notes.append("4Q timing boost")

    # Lead logic
    if lead >= 15:
        probability += 18
        notes.append("Blowout script favors slower finish")
    elif lead >= 10:
        probability += 10
        notes.append("Solid lead supports under")
    elif lead >= 6:
        probability += 4
        notes.append("Moderate lead")
    else:
        probability -= 8
        notes.append("Close game raises foul risk")

    # Time left logic
    if time_left <= 7:
        probability += 8
        notes.append("Late-game clock advantage")
    elif time_left <= 9:
        probability += 4
        notes.append("Good live window")

    # Cushion between live total and your bet line
    cushion = bet_line - current_total
    if cushion >= 28:
        probability += 12
        notes.append("Large scoring cushion")
    elif cushion >= 20:
        probability += 8
        notes.append("Good scoring cushion")
    elif cushion >= 12:
        probability += 3
        notes.append("Moderate scoring cushion")
    else:
        probability -= 6
        notes.append("Thin cushion")

    # Odds note
    if -400 <= odds <= -280:
        notes.append("Odds fit your preferred NBA gate")
    else:
        notes.append("Odds outside preferred NBA gate")

    # Clamp
    probability = max(1, min(probability, 99))

    # Stability / verdict
    if probability >= 80:
        verdict = "EXECUTE BET ✅"
        stability = "Stable"
    elif probability >= 70:
        verdict = "LEAN / SMALLER PLAY ⚠️"
        stability = "Medium"
    else:
        verdict = "PASS ❌"
        stability = "Unstable"

    # Extra foul warning
    if lead <= 8 and quarter == "4Q" and time_left <= 3:
        notes.append("Late foul risk elevated")

    return {
        "probability": probability,
        "verdict": verdict,
        "stability": stability,
        "notes": notes,
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
        "Comparing current total to bet line...",
        "Finalizing probability...",
    ]

    for i in range(100):
        time.sleep(0.02)
        progress_bar.progress(i + 1)

        if i < 15:
            status_text.text(steps[0])
        elif i < 30:
            status_text.text(steps[1])
        elif i < 50:
            status_text.text(steps[2])
        elif i < 70:
            status_text.text(steps[3])
        elif i < 90:
            status_text.text(steps[4])
        else:
            status_text.text(steps[5])

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

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Probability", f"{result['probability']}%")

    with c2:
        st.metric("Stability", result["stability"])

    with c3:
        st.metric("Verdict", result["verdict"])

    st.write(f"**Matchup:** {team_1} vs {team_2}")
    st.write(f"**Bet:** {bet_name}")
    st.write(f"**Quarter:** {quarter}")
    st.write(f"**Time Left:** {time_left}")
    st.write(f"**Lead Margin:** {lead}")
    st.write(f"**Current Total:** {current_total}")
    st.write(f"**Bet Line:** {bet_line}")
    st.write(f"**Odds:** {odds}")

    st.markdown("**Why:**")
    for note in result["notes"]:
        st.write(f"- {note}")

    st.markdown("---")

    # Save analyzed bet to tracker
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
            "Odds": odds,
            "Probability": f"{result['probability']}%",
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
