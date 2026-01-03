from decimal import Decimal
from datetime import datetime, timezone
import time
from .base import BaseScanner

class ParadexScanner(BaseScanner):
    BASE_URL = "https://api.prod.paradex.trade/v1"

    def __init__(self):
        super().__init__("Paradex")

    def fetch_tickers(self):
        url = f"{self.BASE_URL}/markets"
        try:
            # В ответе Paradex данные лежат в ключе 'results'
            data = self._get(url)
            results = []
            for item in data.get('results', []):
                # Берем только бессрочные контракты (PERP)
                if item.get('asset_kind') == 'PERP':
                    results.append({
                        'symbol': item['symbol'],
                        'original_symbol': item['symbol'],
                        'price': Decimal('1.0') # У Paradex цена берется из другого места, для начала поставим заглушку или fetch_prices
                    })
            return results
        except Exception as e:
            print(f"Ошибка Paradex: {e}")
            return []

    def fetch_funding_history(self, original_symbol, lookback_days=30):
        url = f"{self.BASE_URL}/funding/history"
        
        # Paradex использует start_at и end_at (timestamp in ms)
        end_at = int(time.time() * 1000)
        start_at = end_at - (lookback_days * 24 * 3600 * 1000)
        
        params = {
            "market": original_symbol,
            "start_at": start_at,
            "end_at": end_at,
            "page_size": 100 # Пагинация может потребоваться для больших диапазонов
        }
        
        try:
            data = self._get(url, params=params)
            history = []
            
            for item in data.get('results', []):
                # Paradex фандинг часто идет почасовой или 8-часовой, зависит от рынка.
                # Обычно 1 час.
                ts = datetime.fromtimestamp(item['timestamp'] / 1000.0, tz=timezone.utc)
                
                history.append({
                    'timestamp': ts,
                    'rate': Decimal(str(item['funding_rate'])),
                    'period_hours': 1 
                })
            
            return history
        except Exception as e:
            print(f"Error Paradex funding: {e}")
            return []