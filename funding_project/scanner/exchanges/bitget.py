import time
from decimal import Decimal
from datetime import datetime, timezone
from .base import BaseScanner # Обязательно наследуемся от BaseScanner

class BitgetScanner(BaseScanner): # Наследуемся
    TICKERS_URL = "https://api.bitget.com/api/v2/mix/market/tickers"
    FUNDING_URL = "https://api.bitget.com/api/v2/mix/market/history-fund-rate"

    def __init__(self):
        super().__init__("Bitget")

    def fetch_tickers(self):
        params = {"productType": "USDT-FUTURES"}
        try:
            resp = self._get(self.TICKERS_URL, params=params)
            data = resp.get("data")
            if data is None: return []
            
            results = []
            for item in data:
                original = item['symbol']  # Например, "BTCUSDT"
                
                # НОРМАЛИЗАЦИЯ: убираем USDT в конце
                # Если символ "BTCUSDT", останется "BTC"
                clean_symbol = original
                if original.endswith('USDT'):
                    clean_symbol = original[:-4]
                elif original.endswith('USDT_SUMP'): # На всякий случай для экзотики
                    clean_symbol = original.replace('USDT_SUMP', '')

                results.append({
                    'symbol': clean_symbol,          # Для нашей базы (группировки)
                    'original_symbol': original,     # Для будущих запросов к API
                    'price': Decimal(str(item['lastPr']))
                })
            return results
        except Exception as e:
            print(f"Ошибка получения тикеров Bitget: {e}")
            return []

    # БЫЛО: get_funding_history -> СТАЛО: fetch_funding_history
    def fetch_funding_history(self, original_symbol, lookback_days=30):
        # 1. Вычисляем время начала в миллисекундах
        end_time = int(time.time() * 1000)
        start_time = end_time - (lookback_days * 24 * 60 * 60 * 1000)
        
        # Bitget V2 API позволяет до 100 записей. 
        # 30 дней * 3 выплаты = 90 записей. 100 как раз хватает.
        params = {
            "symbol": original_symbol, 
            "productType": "USDT-FUTURES", 
            "limit": 100,
            "startTime": start_time
        }
        
        try:
            resp = self._get(self.FUNDING_URL, params=params)
            data = resp.get("data") or [] 
            
            history = []
            for item in data:
                ts = datetime.fromtimestamp(int(item['fundingTime']) / 1000.0, tz=timezone.utc)
                history.append({
                    'timestamp': ts,
                    'rate': Decimal(str(item['fundingRate'])),
                    'period_hours': 8 
                })
                
            return history
        except Exception as e:
            print(f"Ошибка истории Bitget для {original_symbol}: {e}")
            return []