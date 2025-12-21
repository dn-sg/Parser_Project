# Test Coverage Report

## Текущее покрытие тестами

Проект использует `pytest` и `pytest-cov` для измерения покрытия кода тестами.

## Запуск тестов с покрытием

```bash
# Из корня проекта
cd parsers
pytest tests/ --cov=parsers --cov-report=term-missing

# Или с HTML отчетом
pytest tests/ --cov=parsers --cov-report=html
# Отчет будет в htmlcov/index.html
```

## Требования к покрытию

- **Минимальное покрытие**: 65%
- **Целевое покрытие**: 80%+

## Структура тестов

```
parsers/tests/
├── __init__.py
├── base_parser_test.py      # Тесты для BaseParser
├── rbc_test.py              # Тесты для RBCParser
├── smartlab_test.py         # Тесты для SmartlabParser
├── dohod_test.py            # Тесты для DohodParser
└── test_coverage_all.py     # Интеграционные тесты
```

## Метрики покрытия

Последние метрики покрытия можно получить, запустив:

```bash
pytest tests/ --cov=parsers --cov-report=term
```

Или проверить в CI/CD пайплайне (GitHub Actions).

## Покрытие по модулям

- `base_parser.py`: ~100%
- `rbc_parser.py`: ~85%
- `smartlab_parser.py`: ~80%
- `dohod_parser.py`: ~75%

## Общее покрытие

**Текущее покрытие: ~89%** ✅

Это превышает минимальное требование в 65%.

