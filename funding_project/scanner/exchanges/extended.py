from decimal import Decimal
from datetime import datetime, timezone
import time
from .base import BaseScanner

class ExtendedScanner(BaseScanner):
    # Вставь сюда реальный домен API
    BASE_URL = "https://api.extended-exchange-url.com/v1" 

    def __init__(self):
        super().__init__("Extended")

    def fetch_tickers(self):
        url = f"{self.BASE_URL}/market/tickers" # Стандартный путь
        try:
            data = self._get(url)
            results = []
            
            # Адаптируй парсинг под реальный JSON
            for item in data:
                results.append({
                    'symbol': item['symbol'].replace('_USDT', ''), # Пример очистки
                    'original_symbol': item['symbol'],
                    'price': Decimal(str(item['price']))
                })
            return results
        except Exception as e:
            print(f"Error Extended tickers: {e}")
            return []

    def fetch_funding_history(self, original_symbol, lookback_days=30):
        url = f"{self.BASE_URL}/market/funding/history"
        
        params = {
            "symbol": original_symbol,
            "limit": 50
        }
        
        try:
            data = self._get(url, params=params)
            history = []
            
            for item in data:
                # Пример парсинга времени
                ts = datetime.fromtimestamp(item['time'] / 1000.0, tz=timezone.utc)
                history.append({
                    'timestamp': ts,
                    'rate': Decimal(str(item['fundingRate'])),
                    'period_hours': 8 # Уточни период (1 или 8 часов)
                })
            return history
        except Exception as e:
            print(f"Error Extended funding: {e}")
            return []