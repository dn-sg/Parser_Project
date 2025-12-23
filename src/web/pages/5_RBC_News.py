import streamlit as st
import pandas as pd
from src.utils.api_client import get_json

st.set_page_config(page_title="RBC News", layout="wide")

st.title("📰 RBC Новости")

data = get_json("/api/data/rbc?limit=500")
df = pd.DataFrame(data)

if df.empty:
    st.info("Нет данных.")
    st.stop()

df["parsed_at"] = pd.to_datetime(df["parsed_at"], errors="coerce")

st.subheader("🔍 Фильтры")

c1, c2, c3 = st.columns([2, 3, 3])

with c1:
    limit = st.number_input("Кол-во строк", min_value=20, max_value=500, value=100, step=20)

with c2:
    if df["parsed_at"].notna().any():
        dmin = df["parsed_at"].min().date()
        dmax = df["parsed_at"].max().date()
        date_range = st.date_input("Дата и время", (dmin, dmax))
    else:
        date_range = None

with c3:
    q = st.text_input("title")

df_view = df.copy()

if date_range and len(date_range) == 2:
    start, end = date_range
    df_view = df_view[df_view["parsed_at"].dt.date.between(start, end)]

if q:
    df_view = df_view[df_view["title"].str.contains(q, case=False, na=False)]

df_view = df_view.sort_values(["parsed_at"], ascending=False).head(int(limit))

st.divider()
st.subheader("📋 Новости")

# Таблица для отображения и выбора новости
displayed_df = df_view[["parsed_at", "title"]].copy()
st.dataframe(displayed_df, use_container_width=True)

st.divider()
st.subheader("📖 Просмотр новости")

news_ids = df_view["id"].tolist()
if news_ids:
    selected_id = st.selectbox(
        "Выберите новость для просмотра:",
        options=news_ids,
        format_func=lambda x: df_view[df_view["id"] == x]["title"].values[0] if len(
            df_view[df_view["id"] == x]) > 0 else "N/A"
    )

    # Получаю полный текст новости
    news_detail = get_json(f"/api/rbc_news/{selected_id}")

    if news_detail:
        st.markdown(f"### {news_detail.get('title', 'N/A')}")
        st.markdown(f"**Дата:** {news_detail.get('parsed_at', 'N/A')}")
        st.markdown(f"**URL:** [Ссылка]({news_detail.get('url', '#')})")
        st.divider()
        st.markdown(f"**Текст:**")
        st.markdown(news_detail.get('text', 'Текст не найден'))
    else:
        st.warning("Не удалось загрузить текст новости")
else:
    st.info("Нет новостей для отображения")