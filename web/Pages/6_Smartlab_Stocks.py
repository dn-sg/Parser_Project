import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from _api import get_json

st.set_page_config(page_title="SmartLab Stocks", layout="wide")

st.title("📈 SmartLab Акции")

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
if available_tickers:
    # ✅ ДОБАВЛЕНО: поиск тикера текстом
    ticker_query = st.text_input("Поиск тикера для графика (ввод текста):", value="")

    filtered_tickers = available_tickers
    if ticker_query:
        filtered_tickers = [t for t in available_tickers if ticker_query.lower() in t.lower()]

    if not filtered_tickers:
        st.warning("По вашему запросу тикеры не найдены.")
        st.stop()

    selected_ticker = st.selectbox("Выберите акцию для графика:", filtered_tickers)

    # Фильтруем данные по выбранной акции
    ticker_data = df[df["ticker"] == selected_ticker].sort_values("parsed_at")

    if not ticker_data.empty and "last_price_rub" in ticker_data.columns:
        ticker_data = ticker_data.dropna(subset=["last_price_rub"])
        if not ticker_data.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=ticker_data["parsed_at"],
                y=ticker_data["last_price_rub"],
                mode="lines+markers",
                name="Цена",
                line=dict(color="#2180a0", width=2),
                marker=dict(size=6)
            ))
            fig.update_layout(
                title=f"Динамика цены {selected_ticker}",
                xaxis_title="Дата",
                yaxis_title="Цена (РУБ)",
                hovermode="x unified",
                height=500,
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown(f"**Статистика по {selected_ticker}:**")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Текущая цена", f"{ticker_data['last_price_rub'].iloc[-1]:.2f} РУБ")

            with col2:
                price_change = ticker_data['last_price_rub'].iloc[-1] - ticker_data['last_price_rub'].iloc[0]
                st.metric("Изменение цены", f"{price_change:+.2f} РУБ")

            with col3:
                if "price_change_percent" in ticker_data.columns:
                    change_pct = ticker_data['price_change_percent'].iloc[-1]
                    st.metric("Изменение %", f"{change_pct:+.2f}%")

            with col4:
                if "volume_mln_rub" in ticker_data.columns and ticker_data['volume_mln_rub'].iloc[-1] is not None:
                    volume = ticker_data['volume_mln_rub'].iloc[-1]
                    st.metric("Объем (млн РУБ)", f"{volume:.2f}")
        else:
            st.warning(f"Нет данных по цене для {selected_ticker}")
    else:
        st.warning(f"Недостаточно данных для построения графика {selected_ticker}")
else:
    st.info("Нет доступных акций для отображения графика")
