"""
Парсер для сайта Dohod.ru
"""
from .base_parser import BaseParser
from bs4 import BeautifulSoup
from typing import List, Dict
import re


class DohodParser(BaseParser):
    """Парсер для сайта Dohod.ru"""
    
    def __init__(self):
        super().__init__("https://www.dohod.ru/ik/analytics/share")
    
    def parse(self) -> List[Dict]:
        """
        Парсинг данных с сайта Dohod.ru
        
        Returns:
            Список словарей с данными о компаниях
        """
        html = self.fetch_html()
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        companies = []
        
        try:
            # Поиск таблицы или списка с акциями
            table = soup.find('table', class_=re.compile(r'quote|stock|table|data', re.I))
            if not table:
                # Пробуем найти любую таблицу
                table = soup.find('table')
            
            if table:
                rows = table.find_all('tr')[1:21]  # Пропускаем заголовок
                
                for row in rows:
                    try:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) < 2:
                            continue
                        
                        # Извлечение тикера и названия
                        ticker = ""
                        company_name = ""
                        
                        # Первая или вторая колонка обычно содержит тикер/название
                        for i, cell in enumerate(cells[:3]):
                            text = cell.get_text(strip=True)
                            # Если текст короткий и в верхнем регистре - вероятно тикер
                            if len(text) <= 6 and text.isupper() and not ticker:
                                ticker = text
                            # Если текст длиннее - вероятно название компании
                            elif len(text) > 6 and not company_name:
                                company_name = text
                        
                        if not ticker and len(cells) > 0:
                            ticker = cells[0].get_text(strip=True)
                        if not company_name and len(cells) > 1:
                            company_name = cells[1].get_text(strip=True)
                        
                        # Поиск цены, изменения и объема
                        price = 0.0
                        change = 0.0
                        volume = 0
                        
                        for cell in cells:
                            text = cell.get_text(strip=True)
                            # Проверка на цену (число с точкой/запятой)
                            if re.match(r'^\d+[.,]\d+$', text.replace(' ', '')):
                                if price == 0.0:
                                    price = self._parse_price(text)
                            # Проверка на изменение (содержит + или -)
                            elif re.match(r'^[+-]', text):
                                change = self._parse_change(text)
                            # Проверка на объем (большое число)
                            elif re.match(r'^\d{4,}', text.replace(' ', '')):
                                volume = self._parse_volume(text)
                        
                        if ticker:
                            companies.append({
                                "ticker": ticker,
                                "company_name": company_name or ticker,
                                "price": price,
                                "change": change,
                                "volume": volume,
                                "source": "Dohod"
                            })
                    except Exception as e:
                        print(f"Ошибка при парсинге строки: {e}")
                        continue
            else:
                # Альтернативный способ - поиск по классам/атрибутам
                items = soup.find_all(['div', 'li', 'tr'], 
                                     class_=re.compile(r'quote|stock|share|item|row', re.I))
                
                for item in items[:20]:
                    try:
                        # Поиск тикера
                        ticker_elem = item.find(['span', 'div', 'td'], 
                                               class_=re.compile(r'ticker|symbol|code', re.I))
                        if not ticker_elem:
                            ticker_elem = item.find('strong') or item.find('b')
                        
                        ticker = ticker_elem.get_text(strip=True) if ticker_elem else ""
                        
                        if ticker:
                            # Поиск названия
                            name_elem = item.find(['a', 'span', 'div'], 
                                                 class_=re.compile(r'name|title|company', re.I))
                            company_name = name_elem.get_text(strip=True) if name_elem else ticker
                            
                            companies.append({
                                "ticker": ticker,
                                "company_name": company_name,
                                "price": 0.0,
                                "change": 0.0,
                                "volume": 0,
                                "source": "Dohod"
                            })
                    except Exception as e:
                        print(f"Ошибка при парсинге элемента: {e}")
                        continue
        
        except Exception as e:
            print(f"Ошибка при парсинге Dohod: {e}")
        
        return companies
    
    def _parse_price(self, text: str) -> float:
        """Парсинг цены из текста"""
        try:
            cleaned = re.sub(r'[^\d.,]', '', text.replace(',', '.').replace(' ', ''))
            return float(cleaned) if cleaned else 0.0
        except:
            return 0.0
    
    def _parse_change(self, text: str) -> float:
        """Парсинг изменения цены"""
        try:
            cleaned = re.sub(r'[^\d.,+-]', '', text.replace(',', '.'))
            if '%' in text:
                cleaned = cleaned.replace('%', '')
            if '+' in cleaned and not cleaned.startswith('+'):
                cleaned = cleaned.replace('+', '')
            if '-' in cleaned and not cleaned.startswith('-'):
                cleaned = '-' + cleaned.replace('-', '')
            return float(cleaned) if cleaned else 0.0
        except:
            return 0.0
    
    def _parse_volume(self, text: str) -> int:
        """Парсинг объема торгов"""
        try:
            text = text.upper().replace(' ', '')
            multiplier = 1
            if 'K' in text or 'К' in text:
                multiplier = 1000
                text = text.replace('K', '').replace('К', '')
            elif 'M' in text or 'М' in text:
                multiplier = 1000000
                text = text.replace('M', '').replace('М', '')
            elif 'B' in text or 'Б' in text:
                multiplier = 1000000000
                text = text.replace('B', '').replace('Б', '')
            
            cleaned = re.sub(r'[^\d]', '', text)
            return int(float(cleaned) * multiplier) if cleaned else 0
        except:
            return 0


if __name__ == "__main__":
    parser = DohodParser()
    data = parser.get_parsed_data()
    print(data)

