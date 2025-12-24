import streamlit as st
import pandas as pd
from src.utils.api_client import get_json

st.set_page_config(page_title="Dohod Divs", layout="wide")

st.title("Дивиденды")

data = get_json("/api/data/dohod?limit=2000")
df = pd.DataFrame(data)

if df.empty:
    st.info("Нет данных.")
    st.stop()

if "record_date_estimate" in df.columns:
    df["record_date_estimate"] = pd.to_datetime(df["record_date_estimate"], errors="coerce").dt.date

st.subheader("Фильтры")

c1, c2, c3, c4 = st.columns([2, 4, 2, 4])

with c1:
    limit = st.number_input("Кол-во строк", min_value=50, max_value=2000, value=2000, step=50)

with c2:
    tickers = sorted(df["ticker"].dropna().unique().tolist())
    sel_tickers = st.multiselect("Ticker", tickers, default=[])

with c3:
    if "record_date_estimate" in df.columns and df["record_date_estimate"].notna().any():
        dmin = df["record_date_estimate"].dropna().min()
        dmax = df["record_date_estimate"].dropna().max()
        date_range = st.date_input("Дата и время", (dmin, dmax))
    else:
        date_range = None

with c4:
    sector_list = sorted(df["sector"].dropna().unique().tolist())
    sel_sectors = st.multiselect("sector", sector_list, default=[])

df_view = df.copy()
df_view = df_view.head(int(limit))

if sel_tickers:
    df_view = df_view[df_view["ticker"].isin(sel_tickers)]

if sel_sectors:
    df_view = df_view[df_view["sector"].isin(sel_sectors)]

if date_range and len(date_range) == 2 and "record_date_estimate" in df_view.columns:
    start, end = date_range
    df_view = df_view[df_view["record_date_estimate"].between(start, end)]

st.divider()
st.subheader("Данные")
st.dataframe(df_view, use_container_width=True)