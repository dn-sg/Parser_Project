"""
Обёртка для обратной совместимости
Использует новую архитектуру из commands/
"""
import logging
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from commands.smartlab_parser import SmartlabParser as NewSmartlabParser
from commands.parser_service import ParserService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_smartlab_parser():
    """Функция запуска парсера SmartLab (обратная совместимость)"""
    try:
        parser = NewSmartlabParser()
        ParserService.run_smartlab_parser(parser)
        logger.info("Все операции завершены успешно.")
    except Exception as e:
        logger.error(f"Ошибка при запуске парсера: {e}", exc_info=True)


if __name__ == "__main__":
    run_smartlab_parser()
