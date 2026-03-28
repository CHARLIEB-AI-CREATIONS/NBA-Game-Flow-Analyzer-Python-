import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Tracker Dashboard", layout="wide")

FILE = Path("tracker.csv")

# -----------------------------
# Load data
# -----------------------------
def load_data():
    if FILE.exists():
        df = pd.read_csv(FILE)
    else:
        df = pd.DataFrame(columns=[
            "team",
            "opponent",
            "level",
            "edge_score",
            "probability",
            "bet_placed",
            "result"
        ])
        df.to_csv(FILE, index=False)
    return df

def save_data(df):
    df.to_csv(FILE, index=False)

df = load_data()

st.title("Tracker Dashboard")

# -----------------------------
# Clean values
# -----------------------------
if not df.empty:
    df["bet_placed"] = df["bet_placed"].astype(str).str.lower().str.strip()
    df["result"] = df["result"].astype(str).str.lower().str.strip()

# -----------------------------
# Build game label automatically
# -----------------------------
if "team" in df.columns and "opponent" in df.columns:
    df["game"] = df["team"] + " vs " + df["opponent"]

# -----------------------------
# Editable table
# -----------------------------
st.subheader("Recent Entries")

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    key="tracker_editor",
    column_config={
        "team": st.column_config.TextColumn("Team"),
        "opponent": st.column_config.TextColumn("Opponent"),
        "game": st.column_config.TextColumn("Game", disabled=True),

        "level": st.column_config.SelectboxColumn(
            "level",
            options=["S", "E"]
        ),

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

# -----------------------------
# Save buttons
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("Save Changes"):
        save_data(edited_df)
        st.success("Saved ✅")

with col2:
    if st.button("Reload"):
        st.rerun()

# -----------------------------
# Stats (ONLY placed bets)
# -----------------------------
placed_df = edited_df[edited_df["bet_placed"] == "y"]

graded_df = placed_df[placed_df["result"].isin(["win", "loss", "push"])]

wins = (graded_df["result"] == "win").sum()
losses = (graded_df["result"] == "loss").sum()
pushes = (graded_df["result"] == "push").sum()

decision = wins + losses
win_rate = (wins / decision * 100) if decision > 0 else 0

st.subheader("Stats")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Wins", wins)
c2.metric("Losses", losses)
c3.metric("Pushes", pushes)
c4.metric("Win Rate", f"{win_rate:.1f}%")
