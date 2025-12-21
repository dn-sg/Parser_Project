"""
Пакет парсеров (обёртки для обратной совместимости)
"""
# Импортируем функции запуска парсеров
from .rbc import run_rbc_parser
from .smartlab import run_smartlab_parser
from .dohod import run_dohod_parser

__all__ = ['run_rbc_parser', 'run_smartlab_parser', 'run_dohod_parser']
