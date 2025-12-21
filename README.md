# Parser Project

Проект для парсинга финансовых данных с различных российских сайтов (RBC, SmartLab, Dohod.ru).

## Архитектура

Проект следует архитектуре Д32 с разделением на:
- **models/** - SQLAlchemy модели (доменные сущности)
- **commands/** - Бизнес-логика парсинга (Use Cases)
- **adapters/** - Адаптеры для внешних систем (HTTP, БД)
- **infra/** - Инфраструктура (конфигурация, подключения)

Подробнее см. [ARCHITECTURE.md](ARCHITECTURE.md)

## Особенности

✅ **SOLID принципы** - SRP, OCP соблюдены  
✅ **DRY** - устранено дублирование кода  
✅ **SQLAlchemy** - все запросы через ORM (без RAW SQL)  
✅ **Асинхронная БД** - FastAPI использует async SQLAlchemy  
✅ **Валидация конфигурации** - через Pydantic Settings  
✅ **Test Coverage** - 89% (требование: 65%)  
✅ **ER Диаграмма** - см. [docs/ER_DIAGRAM.md](docs/ER_DIAGRAM.md)  
✅ **DockerHub** - настроена автоматическая публикация образов  

## Установка

### Требования

- Python 3.11+
- PostgreSQL 15+
- Redis
- Docker & Docker Compose

### Локальная установка

```bash
# Клонировать репозиторий
git clone https://github.com/dn-sg/Parser_Project.git
cd Parser_Project

# Создать .env файл
cp .env.example .env
# Отредактировать .env с вашими настройками

# Установить зависимости
cd web
pip install -r requirements.txt
```

### Docker

```bash
# Запустить все сервисы
docker compose up -d --build

# Проверить статус
docker compose ps
```

## Использование

### API Endpoints

- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501

### Запуск парсеров

```python
from parsers.rbc import run_rbc_parser
from parsers.smartlab import run_smartlab_parser
from parsers.dohod import run_dohod_parser

# Запуск парсера
run_rbc_parser()
```

Или через API:

```bash
curl -X POST http://localhost:8000/api/run/rbc
```

## Тестирование

```bash
cd parsers
pytest tests/ --cov=parsers --cov-report=term-missing
```

Текущее покрытие: **89%** ✅

Подробнее см. [COVERAGE.md](COVERAGE.md)

## База данных

Схема БД описана в [docs/ER_DIAGRAM.md](docs/ER_DIAGRAM.md)

### Основные таблицы

- `source` - Источники данных
- `logs` - Логи парсинга
- `rbc_news` - Новости RBC
- `smartlab_stocks` - Акции SmartLab
- `dohod_divs` - Дивиденды Dohod

## DockerHub

Образы автоматически публикуются на DockerHub при push в master.

Настройка описана в [DOCKERHUB.md](DOCKERHUB.md)

## Структура проекта

```
Parser_Project/
├── models/          # SQLAlchemy модели
├── commands/        # Бизнес-логика парсинга
├── adapters/        # Адаптеры (HTTP, БД)
├── infra/           # Инфраструктура
├── parsers/         # Обёртки для обратной совместимости
├── web/             # FastAPI приложение
├── database/        # SQL скрипты
├── docs/            # Документация
└── .github/         # GitHub Actions workflows
```

## Лицензия

MIT

