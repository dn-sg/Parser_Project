import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from _api import get_json

st.set_page_config(page_title="SmartLab Stocks", layout="wide")

st.title("📈 SmartLab Акции")

# Табличные данные (для фильтров/таблицы оставляем быстрый endpoint с limit)
data = get_json("/api/data/smartlab?limit=2000")
df = pd.DataFrame(data)

if df.empty:
    st.info("Нет данных.")
    st.stop()

df["parsed_at"] = pd.to_datetime(df["parsed_at"], errors="coerce")

# ---- ФИЛЬТРЫ ВСЕГДА ВИДНЫ (БЕЗ CHECKBOX) ----
st.subheader("🔍 Фильтры")

c1, c2, c3 = st.columns([2, 4, 4])

with c1:
    limit = st.number_input("Кол-во строк", min_value=50, max_value=2000, value=2000, step=50)

with c2:
    tickers = sorted(df["ticker"].dropna().unique().tolist())
    sel = st.multiselect("Ticker", tickers, default=[])

with c3:
    q = st.text_input("Поиск по name")

# ---- ПРИМЕНЯЕМ ФИЛЬТРЫ ----
df_view = df.copy()
df_view = df_view.head(int(limit))

if sel:
    df_view = df_view[df_view["ticker"].isin(sel)]

if q:
    df_view = df_view[df_view["name"].str.contains(q, case=False, na=False)]

# ---- ТАБЛИЦА НИЖЕ ----
st.divider()
st.subheader("📊 Данные акций")
st.dataframe(df_view, use_container_width=True)

# ---- ГРАФИК ЦЕНЫ ПО ВЫБРАННОЙ АКЦИИ ----
st.divider()
st.subheader("📉 График цены")

available_tickers = sorted(df_view["ticker"].dropna().unique().tolist())

if not available_tickers:
    st.info("Нет доступных акций для отображения графика")
    st.stop()

# ✅ поиск тикера текстом
ticker_query = st.text_input("Поиск тикера для графика (ввод текста):", value="")
filtered_tickers = available_tickers

if ticker_query:
    filtered_tickers = [t for t in available_tickers if ticker_query.lower() in t.lower()]

if not filtered_tickers:
    st.warning("По вашему запросу тикеры не найдены.")
    st.stop()

selected_ticker = st.selectbox("Выберите акцию для графика:", filtered_tickers)

# ---- История по тикеру (полная) ----
history = get_json(f"/api/data/smartlab/history?ticker={selected_ticker}&limit=50000")
ticker_data = pd.DataFrame(history)

if ticker_data.empty:
    st.warning(f"Нет исторических данных для {selected_ticker}")
    st.stop()

ticker_data["parsed_at"] = pd.to_datetime(ticker_data["parsed_at"], errors="coerce")
ticker_data["last_price_rub"] = pd.to_numeric(ticker_data["last_price_rub"], errors="coerce")
ticker_data = ticker_data.dropna(subset=["parsed_at", "last_price_rub"]).sort_values("parsed_at")

if ticker_data.empty:
    st.warning(f"Недостаточно данных для построения графика {selected_ticker}")
    st.stop()

# ---- График ----
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=ticker_data["parsed_at"],
        y=ticker_data["last_price_rub"],
        mode="lines+markers",
        name="Цена",
        line=dict(color="#2180a0", width=2),
        marker=dict(size=6),
    )
)

fig.update_layout(
    title=f"Динамика цены {selected_ticker}",
    xaxis_title="Дата",
    yaxis_title="Цена (РУБ)",
    hovermode="x unified",
    height=500,
    template="plotly_white",
)

st.plotly_chart(fig, use_container_width=True)

# ---- Метрики (текущая, Δ24ч руб, Δ24ч %) ----
last_ts = ticker_data["parsed_at"].max()
cutoff = last_ts - pd.Timedelta(hours=24)

base_candidates = ticker_data[ticker_data["parsed_at"] <= cutoff]
has_24h = not base_candidates.empty

if has_24h:
    base_price = float(base_candidates["last_price_rub"].iloc[-1])
else:
    # Если истории за 24ч нет — fallback на самую раннюю точку (чтобы метрики не "ломались")
    base_price = float(ticker_data["last_price_rub"].iloc[0])

current_price = float(ticker_data["last_price_rub"].iloc[-1])

delta_rub_24h = current_price - base_price
delta_pct_24h = (delta_rub_24h / base_price * 100.0) if base_price != 0 else None

st.markdown(f"**Статистика по {selected_ticker}:**")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Текущая цена", f"{current_price:.2f} РУБ")

with col2:
    st.metric("Изменение, РУБ (24ч)" if has_24h else "Изменение, РУБ", f"{delta_rub_24h:+.2f} РУБ")

with col3:
    if delta_pct_24h is None:
        st.metric("Изменение, % (24ч)" if has_24h else "Изменение, %", "н/д")
    else:
        st.metric("Изменение, % (24ч)" if has_24h else "Изменение, %", f"{delta_pct_24h:+.2f}%")
