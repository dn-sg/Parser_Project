# Архитектура проекта (Д32)

Проект реорганизован согласно архитектуре Д32 с применением принципов SOLID и устранением дублирования кода.

## Структура проекта

```
Parser_Project/
├── models/          # SQLAlchemy модели (доменные сущности)
├── commands/        # Бизнес-логика парсинга (Use Cases)
├── adapters/        # Адаптеры для внешних систем (HTTP, БД)
├── infra/           # Инфраструктура (конфигурация, подключения)
└── parsers/         # Обёртки для обратной совместимости
```

## Принципы архитектуры

### 1. Models (Модели)
- **Назначение**: Доменные сущности, представление данных в БД
- **Технология**: SQLAlchemy ORM
- **Файлы**:
  - `models/source.py` - Источники данных
  - `models/log.py` - Логи парсинга
  - `models/rbc_news.py` - Новости RBC
  - `models/smartlab_stock.py` - Акции SmartLab
  - `models/dohod_dividend.py` - Дивиденды Dohod

### 2. Commands (Команды)
- **Назначение**: Бизнес-логика парсинга (Use Cases)
- **Принципы**: SOLID (SRP, OCP)
- **Файлы**:
  - `commands/base_parser.py` - Базовый класс парсера
  - `commands/rbc_parser.py` - Парсер RBC
  - `commands/smartlab_parser.py` - Парсер SmartLab
  - `commands/dohod_parser.py` - Парсер Dohod
  - `commands/html_extractor.py` - Утилиты для извлечения HTML (DRY)
  - `commands/parser_service.py` - Сервис для запуска парсеров

### 3. Adapters (Адаптеры)
- **Назначение**: Интерфейсы для работы с внешними системами
- **Файлы**:
  - `adapters/http_client.py` - HTTP клиент для получения HTML
  - `adapters/repository.py` - Репозитории для работы с БД через SQLAlchemy

### 4. Infra (Инфраструктура)
- **Назначение**: Конфигурация и подключения
- **Файлы**:
  - `infra/config.py` - Конфигурация приложения
  - `infra/database.py` - Подключение к БД через SQLAlchemy

## Исправленные проблемы

### ✅ 1. Структура Д32
- Создана структура `models/commands/adapters/infra`
- Чёткое разделение ответственности

### ✅ 2. SOLID принципы
- **SRP (Single Responsibility Principle)**: Каждый класс отвечает за одну задачу
  - `BaseParser` - только парсинг HTML
  - `Repository` - только сохранение в БД
  - `HttpClient` - только HTTP запросы
- **OCP (Open/Closed Principle)**: Классы открыты для расширения, закрыты для модификации
  - Новые парсеры создаются через наследование `BaseParser`
  - Новые репозитории создаются через наследование `Repository`

### ✅ 3. DRY (Don't Repeat Yourself)
- Общая логика извлечения HTML вынесена в `HTMLExtractor`
- Общая логика работы с БД вынесена в базовый `Repository`
- Устранено дублирование кода между парсерами

### ✅ 4. SQLAlchemy вместо RAW SQL
- Все запросы к БД выполняются через SQLAlchemy ORM
- Защита от SQL-инъекций встроена в ORM
- Типобезопасность и валидация данных

## Использование

### Запуск парсера (новая архитектура)

```python
from commands.rbc_parser import RBCParser
from commands.parser_service import ParserService

parser = RBCParser()
ParserService.run_rbc_parser(parser)
```

### Запуск парсера (обратная совместимость)

```python
from parsers.rbc import run_rbc_parser

run_rbc_parser()
```

## Миграция

Старые парсеры в `parsers/` теперь являются обёртками над новой архитектурой.
Они автоматически используют новые команды и адаптеры, обеспечивая обратную совместимость.

