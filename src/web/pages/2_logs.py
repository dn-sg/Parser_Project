import streamlit as st
import pandas as pd
from src.utils.api_client import get_json

st.set_page_config(page_title="Logs", layout="wide")
st.title("Logs")

logs = get_json("/api/logs?limit=2000")
df = pd.DataFrame(logs)

if df.empty:
    st.info("Логов пока нет.")
    st.stop()

if "started_at" in df.columns:
    df["started_at"] = pd.to_datetime(df["started_at"], errors="coerce")

c1, c2, c3, c4 = st.columns([2, 3, 3, 2])

with c1:
    limit = st.number_input("Сколько строк показать", min_value=50, max_value=5000, value=2000, step=50)

with c2:
    if "source_name" in df.columns:
        sources = sorted(df["source_name"].dropna().unique().tolist())
        pick = st.multiselect("Источник (пусто = все)", sources, default=[])
    else:
        pick = []

with c3:
    if "status" in df.columns:
        statuses = sorted(df["status"].dropna().unique().tolist())
        pick_status = st.multiselect("Status (пусто = все)", statuses, default=[])
    else:
        pick_status = []

with c4:
    q = st.text_input("Поиск в error_message")

df_view = df.copy()
df_view = df_view.head(int(limit))

if pick:
    df_view = df_view[df_view["source_name"].isin(pick)]

if pick_status:
    df_view = df_view[df_view["status"].isin(pick_status)]

if q and "error_message" in df_view.columns:
    df_view = df_view[df_view["error_message"].fillna("").str.contains(q, case=False, na=False)]

st.dataframe(df_view, use_container_width=True)
