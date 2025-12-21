"""
Обёртка для обратной совместимости
Использует новую архитектуру из commands/
"""
import logging
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from commands.rbc_parser import RBCParser as NewRBCParser
from commands.parser_service import ParserService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_rbc_parser():
    """Функция запуска парсера RBC (обратная совместимость)"""
    try:
        parser = NewRBCParser()
        ParserService.run_rbc_parser(parser)
        logger.info("Все операции завершены успешно.")
    except Exception as e:
        logger.error(f"Ошибка запуска RBC: {e}", exc_info=True)


if __name__ == "__main__":
    run_rbc_parser()
