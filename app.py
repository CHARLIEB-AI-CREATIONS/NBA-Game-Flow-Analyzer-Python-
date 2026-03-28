import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="NBA Live Under Analyzer", layout="wide")

FILE = Path("tracker.csv")

# -----------------------------
# TRACKER HELPERS
# -----------------------------
def load_data():
    if FILE.exists():
        df = pd.read_csv(FILE)
    else:
        df = pd.DataFrame(columns=[
            "team",
            "opponent",
            "_level",
            "edge_score",
            "probability",
            "bet_placed",
            "result"
        ])
        df.to_csv(FILE, index=False)
    return df

def save_data(df):
    df.to_csv(FILE, index=False)

def ensure_tracker_columns(df):
    defaults = {
        "team": "",
        "opponent": "",
        "_level": "",
        "edge_score": 0,
        "probability": 0,
        "bet_placed": "n",
        "result": "pending",
    }
    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default

    df["team"] = df["team"].fillna("").astype(str)
    df["opponent"] = df["opponent"].fillna("").astype(str)
    df["_level"] = df["_level"].fillna("").astype(str)
    df["edge_score"] = pd.to_numeric(df["edge_score"], errors="coerce").fillna(0).astype(int)
    df["probability"] = pd.to_numeric(df["probability"], errors="coerce").fillna(0).astype(int)
    df["bet_placed"] = df["bet_placed"].fillna("n").astype(str).str.lower().str.strip()
    df["result"] = df["result"].fillna("pending").astype(str).str.lower().str.strip()
    return df

df = ensure_tracker_columns(load_data())

# -----------------------------
# ORIGINAL APP HEADER / STYLE
# -----------------------------
st.title("🏀 NBA Live Under Analyzer")
st.caption("Built by Charles Barnes")

st.divider()

# -----------------------------
# ORIGINAL ANALYZER LAYOUT
# -----------------------------
st.header("Game Inputs")

quarter = st.selectbox("Quarter", ["1Q", "2Q", "3Q", "4Q"], index=3)
time_left = st.text_input("Time Left (M:SS)", value="6:30")
total_score = st.number_input("Total Score (both teams)", min_value=0, value=228, step=1)
lead = st.number_input("Lead", min_value=0, value=10, step=1)
live_line = st.number_input("Live Betting Line", min_value=0.0, value=234.50, step=0.5)

# -----------------------------
# SIMPLE PLACEHOLDER LOGIC
# Replace this block with your real original logic if needed
# -----------------------------
points_needed = max(live_line - total_score, 0)
minutes_left = 0.0
try:
    mins, secs = time_left.split(":")
    minutes_left = int(mins) + int(secs) / 60
except:
    minutes_left = 0.0

needed_pace = round(points_needed / minutes_left, 2) if minutes_left > 0 else 0.0

# Example decision logic
if quarter == "4Q" and lead >= 10 and needed_pace >= 1.0:
    decision = "PASS ❌"
    confidence = 15
    foul_risk = "LOW"
    decision_color = "red"
elif quarter == "4Q" and lead >= 10:
    decision = "SAFE ✅"
    confidence = 78
    foul_risk = "LOW"
    decision_color = "green"
else:
    decision = "MONITOR ⚠️"
    confidence = 55
    foul_risk = "MEDIUM"
    decision_color = "orange"

st.header("Final Decision")

if decision_color == "green":
    st.success(f"{decision} — {confidence}%")
elif decision_color == "orange":
    st.warning(f"{decision} — {confidence}%")
else:
    st.error(f"{decision} — {confidence}%")

st.progress(confidence / 100)

st.write(f"**Confidence Level:** {confidence}%")
st.write(f"**Foul Risk:** {foul_risk}")

st.header("Game Breakdown")
c1, c2 = st.columns(2)
with c1:
    st.metric("Points Needed", f"{points_needed:.1f}")
    st.metric("Time Left", time_left)
with c2:
    st.metric("Needed Pace", f"{needed_pace:.2f}")
    st.metric("Lead", int(lead))

st.divider()

# -----------------------------
# TRACKER SECTION
# -----------------------------
st.title("Tracker Dashboard")
st.subheader("Recent Entries")

edited_df = st.data_editor(
    df[["team", "opponent", "_level", "edge_score", "probability", "bet_placed", "result"]],
    use_container_width=True,
    num_rows="dynamic",
    key="tracker_editor",
    column_config={
        "team": st.column_config.TextColumn("team"),
        "opponent": st.column_config.TextColumn("opponent"),
        "_level": st.column_config.TextColumn("_level"),
        "edge_score": st.column_config.NumberColumn("edge_score", step=1),
        "probability": st.column_config.NumberColumn("probability", step=1),
        "bet_placed": st.column_config.SelectboxColumn(
            "bet_placed",
            options=["y", "n"]
        ),
        "result": st.column_config.SelectboxColumn(
            "result",
            options=["pending", "win", "loss", "push"]
        ),
    },
)

col1, col2 = st.columns(2)

with col1:
    if st.button("Save Changes"):
        save_data(edited_df)
        st.success("Saved.")

with col2:
    if st.button("Reload"):
        st.rerun()

st.subheader("Stats")

placed_df = edited_df[edited_df["bet_placed"] == "y"].copy()
graded_df = placed_df[placed_df["result"].isin(["win", "loss", "push"])].copy()

wins = int((graded_df["result"] == "win").sum())
losses = int((graded_df["result"] == "loss").sum())
pushes = int((graded_df["result"] == "push").sum())

decision_bets = wins + losses
win_rate = (wins / decision_bets * 100) if decision_bets > 0 else 0.0

s1, s2, s3, s4 = st.columns(4)
with s1:
    st.metric("Wins", wins)
with s2:
    st.metric("Losses", losses)
with s3:
    st.metric("Pushes", pushes)
with s4:
    st.metric("Win Rate", f"{win_rate:.1f}%")
