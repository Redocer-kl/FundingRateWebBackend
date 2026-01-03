import requests
from decimal import Decimal
from datetime import datetime, timezone

class BitgetScanner:
    # Используем v2, так как он более стабилен для фандинга
    TICKERS_URL = "https://api.bitget.com/api/v2/mix/market/tickers?productType=USDT-FUTURES"
    FUNDING_URL = "https://api.bitget.com/api/v2/mix/market/history-fund-rate"

    def get_tickers(self):
        print("Скачиваем цены с Bitget...")
        resp = requests.get(self.TICKERS_URL, timeout=10).json()
        data = resp.get("data", [])
        
        results = []
        for item in data:
            results.append({
                'symbol': item['symbol'], # Например 'BTCUSDT'
                'price': Decimal(str(item['lastPr']))
            })
        return results

    def get_funding_history(self, symbol):
        # Для начала берем последнюю запись. 
        # API Bitget требует limit, возьмем последние 10 записей для истории.
        params = {"symbol": symbol, "limit": 10}
        resp = requests.get(self.FUNDING_URL, params=params, timeout=10).json()
        data = resp.get("data", [])
        
        history = []
        for item in data:
            ts = datetime.fromtimestamp(int(item['fundingTime']) / 1000.0, tz=timezone.utc)
            history.append({
                'timestamp': ts,
                'rate': Decimal(str(item['fundingRate'])),
                'period_hours': 8 # У Bitget стандарт 8 часов
            })
        return history