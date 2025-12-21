"""
Адаптеры: интерфейсы для работы с внешними системами
"""
from .http_client import HttpClient
from .repository import Repository, RBCNewsRepository, SmartlabStockRepository, DohodDividendRepository

__all__ = [
    'HttpClient',
    'Repository',
    'RBCNewsRepository',
    'SmartlabStockRepository',
    'DohodDividendRepository',
]

