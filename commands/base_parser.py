"""
Базовый класс для всех парсеров (SOLID: SRP, OCP)
"""
from abc import ABC, abstractmethod
from typing import List, Dict
import json
from adapters.http_client import HttpClient, IHttpClient


class BaseParser(ABC):
    """
    Базовый класс для всех парсеров.
    Применяет принципы SOLID:
    - SRP: отвечает только за парсинг HTML
    - OCP: открыт для расширения через наследование
    """
    
    def __init__(self, url: str, http_client: IHttpClient = None):
        """
        Инициализация парсера
        
        Args:
            url: URL страницы для парсинга
            http_client: HTTP клиент (для тестирования можно передать mock)
        """
        self.url = url
        self.http_client = http_client or HttpClient()
    
    def fetch_html(self) -> str:
        """
        Получение HTML содержимого страницы
        
        Returns:
            HTML содержимое
            
        Raises:
            ValueError: если не удалось получить HTML
        """
        html = self.http_client.get_html(self.url)
        if not html:
            raise ValueError(f"Не удалось получить HTML с {self.url}")
        return html
    
    @abstractmethod
    def parse(self) -> List[Dict]:
        """
        Основной метод парсинга. Должен быть реализован в дочерних классах
        
        Returns:
            Список словарей с данными
        """
        pass
    
    def to_json(self, data: List[Dict]) -> str:
        """
        Преобразование данных в JSON строку
        
        Args:
            data: Список словарей с данными
            
        Returns:
            JSON строка
        """
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def get_parsed_data(self) -> str:
        """
        Получение данных в формате JSON
        
        Returns:
            JSON строка с данными
        """
        data = self.parse()
        return self.to_json(data)

