#!/usr/bin/env python3
"""
Главный файл для запуска парсеров
"""
import sys
import json
from parsers.rbc import RBCParser


def main():
    """Запуск парсера РБК"""
    parser = RBCParser()
    data = parser.get_parsed_data()
    
    # Выводим результат в формате JSON
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

