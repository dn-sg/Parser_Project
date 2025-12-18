"""
Пакет парсеров для использования в веб-приложении
"""
# Импорт парсеров из корневой папки parsers
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from parsers.rbc import RBCParser
from parsers.smartlab import SmartlabParser
from parsers.dohod import DohodParser

__all__ = ['RBCParser', 'SmartlabParser', 'DohodParser']

