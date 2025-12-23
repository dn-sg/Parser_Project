# Описание проекта Parser Project


## Основные возможности

### Парсеры данных

Проект включает в себя 3 парсера:

1. **RBC News Parser** 
   - Парсит новости с сайта РБК (rbc.ru)
   - Извлекает заголовки и полный текст статей
   - Находит ссылки на новости на главной странице
   - Переходит по каждой ссылке и извлекает контент
   - Фильтрует рекламу и служебную информацию

2. **SmartLab Parser** 
   - Парсит данные об акциях с сайта SmartLab (smart-lab.ru)
   - Извлекает информацию о компаниях: название, тикер, цена, изменение цены
   - Собирает данные об объеме торгов и капитализации
   - Обрабатывает числовые данные (цены, проценты)

3. **Dohod Dividends Parser** 
   - Парсит информацию о дивидендах с сайта Dohod.ru
   - Извлекает данные о компаниях, тикерах, секторах
   - Собирает информацию о выплатах дивидендов
   - Обрабатывает даты и финансовые показатели

### Архитектура проекта


```
.
├── infra/
│   └── docker/
│       ├── api.dockerfile
│       ├── web.dockerfile
│       └── worker.dockerfile
├── src/
│   ├── api/
│   │   └── main.py
│   ├── core/
│   │   └── config.py
│   ├── database/
│   │   └── init.sql
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── sources/
│   │       ├── __init__.py
│   │       ├── base_parser.py
│   │       ├── dohod.py
│   │       ├── dohod_divs.json
│   │       ├── rbc.py
│   │       ├── rbc_news.json
│   │       ├── smartlab.py
│   │       └── smartlab_stocks.json
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   ├── db_utils.py
│   │   └── parser_tasks.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── api_client.py
│   └──web/
│       ├── __init__.py
│       ├── main.py
│       └── pages/
│            ├── 1_Dash.py
│            ├── 2_Logs.py
│            ├── 3_Dohod_Divs.py
│            ├── 4_RBC_News.py
│            └── 5_Smartlab_Stocks.py
├── tests/
│   ├── __init__.py
│   └── parsers/
│       ├── __init__.py
│       ├── base_parser_test.py
│       ├── dohod_test.py
│       ├── rbc_test.py
│       ├── smartlab_test.py
│       └── test_coverage_all.py
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── requirements.txt

```


### База данных


- **source** — таблица источников данных
- **logs** — логирование работы парсеров
- **rbc_news** — новости с РБК
- **smartlab_stocks** — данные об акциях
- **dohod_divs** — информация о дивидендах

### Celery
используется для фоновой обработки задач парсинга:

- Задачи выполняются асинхронно
- Логирование всех операций
- Обработка ошибок
- Мониторинг через Flower

### Веб

**Streamlit Dashboard**:
- **main** — приветствующая страница с контактной информацией
- **Dash** — запуск парсеров, краткая стата по парсерам, активность парсеров
- **Logs** — логи парсеров с фильтрами
- **Dohod Divs** — дивиденды с фильтрами
- **RBC News** — новости в общей таблице с фильтрами с возможностью просмотра конкретной новости
- **Smartlab Stocks** — просмотр акций, графики цен

### API

**FastAPI**

- `POST /api/run/{source}` — запуск парсера (smartlab / rbc / dohod)
- `GET /api/task/{task_id}` — статус задачи
- `GET /api/stats` — статистика по данным
- `GET /api/data/{source}` — получение данных
- `GET /api/logs` — получение логов
- `GET /api/status` — статус парсеров


## Сервисы


1. **db** — PostgreSQL база данных
2. **redis** — Redis для Celery
3. **web** — FastAPI сервер (порт 8000)
4. **celery_worker** — Celery worker для выполнения задач
5. **flower** — Flower для мониторинга Celery (порт 5555)
6. **dashboard** — Streamlit дашборд (порт 8501)


## Доступ к сервисам

- **API**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501
- **Flower**: http://localhost:5555


## Запуск проекта


### Запуск докера


   ```
   docker compose up -d --build
   ```

### Статусы сервисов
```
docker compose ps
```

## Тестирование

### Запуск тестов
```
make test              # Сами тесты
make test-cov         # Покрытие
```



## Остановка докера
```
docker compose stop
docker compose down
```

