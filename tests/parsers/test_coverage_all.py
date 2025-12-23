import coverage
import pathlib
import pytest
import io


def test_coverage_all_parsers() -> None:
    """Test coverage for all parsers"""
    this_file = pathlib.Path(__file__).resolve()
    test_dir = this_file.parent
    tests_root = test_dir.parent
    project_root = tests_root.parent

    parsers_dir = project_root / "src" / "parsers" / "sources"

    test_files = [
        test_dir / "base_parser_test.py",
        test_dir / "dohod_test.py",
        test_dir / "rbc_test.py",
        test_dir / "smartlab_test.py",
    ]

    cov = coverage.Coverage()
    cov.start()
    for test_file in test_files:
        pytest.main(["-q", str(test_file)])
    cov.stop()
    cov.save()

    parser_files = [
        parsers_dir / "base_parser.py",
        parsers_dir / "dohod.py",
        parsers_dir / "rbc.py",
        parsers_dir / "smartlab.py",
    ]

    sink = io.StringIO()
    total_report = float(cov.report(include=[str(f) for f in parser_files], file=sink))

    print(f"{total_report:.2f}")
