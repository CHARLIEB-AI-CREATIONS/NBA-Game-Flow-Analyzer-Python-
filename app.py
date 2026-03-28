import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Tracker Dashboard", layout="wide")

FILE = Path("tracker.csv")

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

df = load_data()

# Add missing columns (no layout change)
for col, default in {
    "team": "",
    "opponent": "",
    "_level": "",
    "edge_score": 0,
    "probability": 0,
    "bet_placed": "n",
    "result": "pending"
}.items():
    if col not in df.columns:
        df[col] = default

# Clean data
df["team"] = df["team"].fillna("").astype(str)
df["opponent"] = df["opponent"].fillna("").astype(str)
df["_level"] = df["_level"].fillna("").astype(str)
df["edge_score"] = pd.to_numeric(df["edge_score"], errors="coerce").fillna(0).astype(int)
df["probability"] = pd.to_numeric(df["probability"], errors="coerce").fillna(0).astype(int)
df["bet_placed"] = df["bet_placed"].fillna("n").astype(str).str.lower().str.strip()
df["result"] = df["result"].fillna("pending").astype(str).str.lower().str.strip()

st.title("Tracker Dashboard")
st.subheader("Recent Entries")

edited_df = st.data_editor(
    df,
    use_container_width=True,
    num_rows="dynamic",
    key="tracker_editor",
    column_config={
        "team": st.column_config.TextColumn("Team (you can type 'Lakers vs Suns')"),
        "opponent": st.column_config.TextColumn("Opponent (optional)"),
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

if st.button("Save Changes"):
    save_data(edited_df)
    st.success("Saved.")

if st.button("Reload"):
    st.rerun()

st.subheader("Stats")

placed_df = edited_df[edited_df["bet_placed"] == "y"]
graded_df = placed_df[placed_df["result"].isin(["win", "loss", "push"])]

wins = (graded_df["result"] == "win").sum()
losses = (graded_df["result"] == "loss").sum()
pushes = (graded_df["result"] == "push").sum()

decision = wins + losses
win_rate = (wins / decision * 100) if decision > 0 else 0

st.metric("Wins", wins)
st.metric("Losses", losses)
st.metric("Pushes", pushes)
st.metric("Win Rate", f"{win_rate:.1f}%")
