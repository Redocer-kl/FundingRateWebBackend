from decimal import Decimal
from datetime import datetime, timezone
from .base import BaseScanner

class ApexScanner(BaseScanner):
    # Используем API Apex Pro
    TICKERS_URL = "https://pro.apex.exchange/api/v1/symbols" 
    FUNDING_URL = "https://pro.apex.exchange/api/v1/funding-rate-history"

    def __init__(self):
        super().__init__("Apex")

    def fetch_tickers(self):
        url = f"{self.TICKERS_URL}"
        try:
            data = self._get(url)
            # Структура: {'code': '0', 'data': [...]}
            if data.get('code') != '0':
                return []
                
            results = []
            for item in data['data']:
                # item: {'symbol': 'BTCUSDC', 'lastPrice': '...', ...}
                symbol = item['symbol']
                # Apex тикеры обычно заканчиваются на USDC, уберем для красоты, если нужно
                # но лучше хранить оригинальный
                
                results.append({
                    'symbol': symbol,
                    'original_symbol': symbol,
                    'price': Decimal(str(item['lastPrice']))
                })
            return results
        except Exception as e:
            print(f"Error fetching Apex tickers: {e}")
            return []

    def fetch_funding_history(self, original_symbol, lookback_days=30):
        # Endpoint: /api/v1/funding/history
        url = f"{self.FUNDING_URL}"
        
        # Apex требует пагинацию или лимит. По умолчанию дает немного.
        # Для простоты возьмем последние 100 записей (это примерно 4 дня, т.к. фандинг каждый час)
        # Если нужно 30 дней, придется делать цикл с offset/page.
        
        limit = 200 # Максимум за раз
        params = {
            "symbol": original_symbol,
            "limit": limit
        }
        
        try:
            data = self._get(url, params=params)
            if data.get('code') != '0':
                return []
            
            history = []
            rows = data['data']['list'] # У Apex список часто внутри data.list
            
            for item in rows:
                # item: {'symbol': 'BTCUSDC', 'fundingRate': '0.0001', 'fundingTime': '16...'}
                ts_ms = int(item['fundingTime'])
                ts = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
                
                history.append({
                    'timestamp': ts,
                    'rate': Decimal(str(item['fundingRate'])),
                    'period_hours': 1 # Apex обычно почасовой
                })
                
            return history
        except Exception as e:
            print(f"Error fetching Apex funding for {original_symbol}: {e}")
            return []