import streamlit as st

st.set_page_config(
    page_title="Parser Dashboards",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Parser Project")

st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Основной функционал")
    
    st.markdown("**RBC News Parser**")
    st.markdown("- Парсинг новостей с сайта РБК")
    st.markdown("- Извлечение заголовков и полного текста статей")
    st.markdown("- Фильтрация дублирующихся новостей и рекламы")
    
    st.markdown("**SmartLab Parser**")
    st.markdown("- Сбор данных об акциях с SmartLab")
    st.markdown("- Данные об объеме торгов и капитализации")
    st.markdown("- Построение графиков по данным из бд")
    
    st.markdown("**Dohod Divs Parser**")
    st.markdown("- Парсинг информации о дивидендах с Dohod.ru")
    st.markdown("- Данные о выплатах и финансовых показателях")

with col2:
    st.markdown("## Команда проекта")
    
    team_members = [
        {"name": "Сергунов Даниил", "telegram": "@Dan_DS"},
        {"name": "Дерлугов Сергей", "telegram": "@Sergeyder1"},
        {"name": "Мамедов Африн", "telegram": "@Afrin4ik"},
        {"name": "Иванов Михаил", "telegram": "@dabl_dog"}
    ]
    
    for member in team_members:
        st.markdown(f"**{member['name']}**")
        st.markdown(f"Telegram: `{member['telegram']}`")
        st.markdown("")

