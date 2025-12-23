# Parser Project

Проект для парсинга финансовых новостей и данных об акциях.

## Структура проекта

```
src/
├── __init__.py
├── core/
│   ├── __init__.py
│   └── config.py
├── api/
│   ├── __init__.py
│   ├── main.py
│   └── routes/
├── web/
│   ├── __init__.py
│   ├── main.py
│   └── pages/
├── parsers/
│   ├── __init__.py
│   └── sources/
├── tasks/
├── services/
├── database/
└── utils/

infra/
└── docker/
    ├── api.dockerfile
    ├── web.dockerfile
    └── worker.dockerfile

tests/
docs/
scripts/

.env.example
docker-compose.yml
pyproject.toml
requirements.txt
Makefile
README.md
```

## Установка и запуск

1. Скопируйте `.env.example` в `.env` и настройте переменные окружения
2. Запустите проект через Docker Compose:
   ```bash
   docker compose up -d --build
   ```

## Использование

- API: http://localhost:8000/docs
- Dashboard: http://localhost:8501
- Flower (Celery): http://localhost:5555

## Команды

См. `Makefile` для доступных команд:
- `make build` - собрать Docker образы
- `make up` - запустить все сервисы
- `make down` - остановить все сервисы
- `make test` - запустить тесты

