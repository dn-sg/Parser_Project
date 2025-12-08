"""
Пакет парсеров для различных сайтов
"""
from .rbc import RBCParser
from .smartlab import SmartLabParser
from .dohod import DohodParser

__all__ = ['RBCParser', 'SmartLabParser', 'DohodParser']

