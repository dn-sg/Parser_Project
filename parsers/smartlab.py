"""
Парсер для сайта SmartLab
"""
from .base_parser import BaseParser
from bs4 import BeautifulSoup
from typing import List, Dict
import re


class SmartLabParser(BaseParser):
    """Парсер для сайта SmartLab"""
    
    def __init__(self):
        super().__init__("https://smart-lab.ru/q/shares/")
    
    def parse(self) -> List[Dict]:
        """
        Парсинг данных с сайта SmartLab
        
        Returns:
            Список словарей с данными о компаниях
        """
        html = self.fetch_html()
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        companies = []
        
        try:
            # Поиск таблицы с акциями
            # Адаптируйте селекторы под реальную структуру сайта
            table = soup.find('table', class_=re.compile(r'quote|stock|table', re.I))
            if not table:
                table = soup.find('table')
            
            if table:
                rows = table.find_all('tr')[1:21]  # Пропускаем заголовок, берем первые 20
                
                for row in rows:
                    try:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) < 3:
                            continue
                        
                        # Извлечение данных из ячеек
                        ticker = cells[0].get_text(strip=True) if len(cells) > 0 else ""
                        company_name = cells[1].get_text(strip=True) if len(cells) > 1 else ticker
                        
                        # Поиск цены (может быть в разных колонках)
                        price = 0.0
                        change = 0.0
                        volume = 0
                        
                        for i, cell in enumerate(cells[2:], start=2):
                            text = cell.get_text(strip=True)
                            # Проверяем, является ли это ценой
                            if re.match(r'^\d+[.,]\d+$', text.replace(' ', '')):
                                price = self._parse_price(text)
                            # Проверяем, является ли это изменением
                            elif re.match(r'^[+-]?\d+[.,]?\d*%?$', text):
                                change = self._parse_change(text)
                            # Проверяем, является ли это объемом
                            elif re.match(r'^\d+[KMB]?$', text, re.I):
                                volume = self._parse_volume(text)
                        
                        if ticker:
                            companies.append({
                                "ticker": ticker,
                                "company_name": company_name,
                                "price": price,
                                "change": change,
                                "volume": volume,
                                "source": "SmartLab"
                            })
                    except Exception as e:
                        print(f"Ошибка при парсинге строки: {e}")
                        continue
            else:
                # Альтернативный способ поиска данных
                quote_elements = soup.find_all(['div', 'li'], class_=re.compile(r'quote|stock|item', re.I))
                for element in quote_elements[:20]:
                    try:
                        ticker_elem = element.find(['span', 'div'], class_=re.compile(r'ticker|symbol', re.I))
                        ticker = ticker_elem.get_text(strip=True) if ticker_elem else ""
                        
                        if ticker:
                            name_elem = element.find(['a', 'span'], class_=re.compile(r'name|title', re.I))
                            company_name = name_elem.get_text(strip=True) if name_elem else ticker
                            
                            companies.append({
                                "ticker": ticker,
                                "company_name": company_name,
                                "price": 0.0,
                                "change": 0.0,
                                "volume": 0,
                                "source": "SmartLab"
                            })
                    except Exception as e:
                        print(f"Ошибка при парсинге элемента: {e}")
                        continue
        
        except Exception as e:
            print(f"Ошибка при парсинге SmartLab: {e}")
        
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
                # Если это процент, убираем знак процента
                cleaned = cleaned.replace('%', '')
            if '+' in cleaned:
                cleaned = cleaned.replace('+', '')
            if '-' in cleaned and not cleaned.startswith('-'):
                cleaned = '-' + cleaned.replace('-', '')
            return float(cleaned) if cleaned else 0.0
        except:
            return 0.0
    
    def _parse_volume(self, text: str) -> int:
        """Парсинг объема торгов"""
        try:
            text = text.upper()
            multiplier = 1
            if 'K' in text:
                multiplier = 1000
                text = text.replace('K', '')
            elif 'M' in text:
                multiplier = 1000000
                text = text.replace('M', '')
            elif 'B' in text:
                multiplier = 1000000000
                text = text.replace('B', '')
            
            cleaned = re.sub(r'[^\d]', '', text)
            return int(float(cleaned) * multiplier) if cleaned else 0
        except:
            return 0


if __name__ == "__main__":
    parser = SmartLabParser()
    data = parser.get_parsed_data()
    print(data)

