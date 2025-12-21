#!/usr/bin/env python3
"""
Главный файл для запуска парсеров
"""
import sys
import json
from parsers.rbc import RBCParser
from parsers.dohod import DohodParser


def main():
    """Запуск парсера РБК"""
    parser = DohodParser()
    print(parser.get_parsed_data())


if __name__ == "__main__":
    main()


