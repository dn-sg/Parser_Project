import streamlit as st
import pandas as pd
from src.utils.api_client import get_json, post_json

st.set_page_config(page_title="Dashboard", layout="wide")

st.title("📊 Главный Дашборд")

# Запуск парсеров по кнопке
st.subheader("🚀 Запуск парсеров")

b1, b2, b3 = st.columns(3)

if b1.button("Запустить SmartLab", use_container_width=True):
    res = post_json("/api/run/smartlab")
    st.success(f"SmartLab запущен, task_id={res.get('task_id')}")

if b2.button("Запустить RBC", use_container_width=True):
    res = post_json("/api/run/rbc")
    st.success(f"RBC запущен, task_id={res.get('task_id')}")

if b3.button("Запустить Dohod", use_container_width=True):
    res = post_json("/api/run/dohod")
    st.success(f"Dohod запущен, task_id={res.get('task_id')}")
st.divider()

# Получаю статистику
try:
    stats = get_json("/api/stats")
    status_data = get_json("/api/status")
except Exception as e:
    st.error(f"Ошибка загрузки данных: {e}")
    st.stop()

# Статистика
st.subheader("📈 Статистика собираемых данных")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("SmartLab Stocks", f"{stats.get('smartlab_total', 0):,}")

with col2:
    st.metric("RBC News", f"{stats.get('rbc_total', 0):,}")

with col3:
    st.metric("Dohod Divs", f"{stats.get('dohod_total', 0):,}")

st.divider()

# Статус парсеров
st.subheader("⚙️ Статус парсеров")

status_df = pd.DataFrame(status_data)

# Форматирую таблицу
display_cols = ["name", "url", "status", "started_at", "duration_seconds"]
if all(col in status_df.columns for col in display_cols):
    status_display = status_df[display_cols].copy()
    status_display.columns = ["Название", "URL", "Статус", "Начало", "Длительность (сек)"]

    # Форматирую статус цветом
    def status_color(status):
        if status == "SUCCESS":
            return "🟢 SUCCESS"
        elif status == "FAILED":
            return "🔴 FAILED"
        elif status == "RUNNING":
            return "🟡 RUNNING"
        else:
            return f"⚪ {status}"

    status_display["Статус"] = status_display["Статус"].apply(status_color)

    st.dataframe(status_display, use_container_width=True)
else:
    st.dataframe(status_df, use_container_width=True)

st.divider()

st.info("💡 Перейдите в меню слева для просмотра деталей по каждому источнику данных")
