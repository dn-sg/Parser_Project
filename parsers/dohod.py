"""
Обёртка для обратной совместимости
Использует новую архитектуру из commands/
"""
import logging
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from commands.dohod_parser import DohodParser as NewDohodParser
from commands.parser_service import ParserService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_dohod_parser():
    """Функция запуска парсера Dohod (обратная совместимость)"""
    try:
        parser = NewDohodParser()
        ParserService.run_dohod_parser(parser)
        logger.info("Готово.")
    except Exception as e:
        logger.error(f"Ошибка запуска: {e}", exc_info=True)


if __name__ == "__main__":
    run_dohod_parser()
