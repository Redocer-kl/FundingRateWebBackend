import requests
import time
from decimal import Decimal
from datetime import datetime, timezone

class BitgetScanner:
    # Используем v2
    TICKERS_URL = "https://api.bitget.com/api/v2/mix/market/tickers"
    FUNDING_URL = "https://api.bitget.com/api/v2/mix/market/history-fund-rate"

    def get_tickers(self):
        print("Скачиваем цены с Bitget...")
        # Указываем productType явно
        params = {"productType": "USDT-FUTURES"}
        try:
            resp = requests.get(self.TICKERS_URL, params=params, timeout=10).json()
            data = resp.get("data")
            
            # Защита от None
            if data is None:
                return []
            
            results = []
            for item in data:
                results.append({
                    'symbol': item['symbol'], 
                    'price': Decimal(str(item['lastPr']))
                })
            return results
        except Exception as e:
            print(f"Ошибка получения тикеров Bitget: {e}")
            return []

    def get_funding_history(self, symbol):
        # Добавляем небольшую задержку, чтобы не получить бан по IP
        time.sleep(0.1)
        
        # ВАЖНО: Bitget V2 требует productType и для истории
        params = {
            "symbol": symbol, 
            "productType": "USDT-FUTURES", 
            "limit": 10
        }
        
        try:
            resp = requests.get(self.FUNDING_URL, params=params, timeout=10).json()
            
            # ИСПРАВЛЕНИЕ ОШИБКИ:
            # Если data придет как None, мы заменим его на пустой список
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
            print(f"Ошибка истории Bitget для {symbol}: {e}")
            return []