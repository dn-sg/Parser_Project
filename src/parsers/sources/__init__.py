"""
Пакет парсеров для различных сайтов
"""
from .rbc import RBCParser
from .smartlab import SmartlabParser
from .dohod import DohodParser

__all__ = ['RBCParser', 'SmartlabParser', 'DohodParser']

