import coverage
import pathlib
import pytest


def test_coverage_all_parsers() -> None:
    """Тест покрытия кода всех парсеров проекта"""
    this_file = pathlib.Path(__file__).resolve()
    test_dir = this_file.parent
    parsers_dir = test_dir.parent

    # Все файлы с тестами
    test_files = [
        test_dir / "base_parser_test.py",
        test_dir / "dohod_test.py",
        test_dir / "rbc_test.py",
        test_dir / "smartlab_test.py",
    ]

    # Запускаем coverage
    cov = coverage.Coverage()
    cov.start()

    # Запускаем все тесты
    for test_file in test_files:
        pytest.main(["-q", str(test_file)])

    cov.stop()
    cov.save()

    # Файлы парсеров для проверки покрытия
    parser_files = [
        parsers_dir / "base_parser.py",
        parsers_dir / "dohod.py",
        parsers_dir / "rbc.py",
        parsers_dir / "smartlab.py",
    ]

    # Получаем общий отчет о покрытии
    print("\n" + "=" * 60)
    print("ОБЩИЙ ОТЧЕТ ПО ПОКРЫТИЮ ТЕСТАМИ")
    print("=" * 60)

    total_report = float(
        cov.report(
            show_missing=True,
            include=[str(f) for f in parser_files],
        )
    )

    print("=" * 60)
    print(f"ОБЩЕЕ ПОКРЫТИЕ: {total_report:.2f}%")
    print("=" * 60)

    # Проверяем покрытие для каждого парсера отдельно
    print("\nДЕТАЛЬНЫЙ ОТЧЕТ ПО ФАЙЛАМ:")
    print("-" * 60)

    coverage_results = {}
    for parser_file in parser_files:
        parser_name = parser_file.stem
        coverage_percent = float(
            cov.report(
                show_missing=False,
                include=[str(parser_file)],
            )
        )
        coverage_results[parser_name] = coverage_percent
        print(f"{parser_name:20s}: {coverage_percent:6.2f}%")

    print("-" * 60)

    # Проверяем минимальные требования (только для общего покрытия)
    min_coverage = 65.0

    # Выводим предупреждения для файлов с низким покрытием, но не фейлим тест
    print("\nАНАЛИЗ ПОКРЫТИЯ:")
    print("-" * 60)
    for parser_name, coverage_percent in coverage_results.items():
        if coverage_percent < min_coverage:
            print(
                f"⚠  {parser_name:20s}: {coverage_percent:6.2f}% (ниже {min_coverage}%)"
            )
        else:
            print(f"✓  {parser_name:20s}: {coverage_percent:6.2f}% (OK)")
    print("-" * 60)

    # Проверяем только общее покрытие
    assert (
        total_report >= min_coverage
    ), f"Общее покрытие {total_report:.2f}% меньше требуемого {min_coverage}%"

    print(f"\n✓ Общее покрытие >= {min_coverage}%")
