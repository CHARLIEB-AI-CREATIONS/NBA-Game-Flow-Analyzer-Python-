import streamlit as st

def evaluate_game(total_score, lead, time_left):
    if lead >= 15 and total_score < 200:
        return "Favorable ✅"
    elif 8 <= lead <= 14:
        return "Caution ⚠️"
    elif total_score > 210:
        return "Avoid ❌"
    else:
        return "Pass"


st.title("NBA Game Flow Dashboard")

st.subheader("Enter Game Data")

team_a = st.number_input("Team A Score", min_value=0, value=100)
team_b = st.number_input("Team B Score", min_value=0, value=90)
time_left = st.number_input("Minutes Left", min_value=0.0, value=6.0)

total_score = team_a + team_b
lead = abs(team_a - team_b)

decision = evaluate_game(total_score, lead, time_left)

st.subheader("Game Analysis")

st.metric("Total Score", total_score)
st.metric("Lead", lead)
st.metric("Decision", decision)
