import requests
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal

class HyperliquidScanner:
    BASE_URL = "https://api.hyperliquid.xyz/info"
    HEADERS = {"Content-Type": "application/json"}

    def __init__(self):
        self.session = requests.Session() # Используем сессию для ускорения

    def _post(self, payload):
        # Добавим небольшую задержку перед каждым запросом
        time.sleep(0.2) 
        try:
            response = self.session.post(self.BASE_URL, json=payload, headers=self.HEADERS, timeout=10)
            if response.status_code == 429:
                print("Rate limit hit! Sleeping 5 seconds...")
                time.sleep(5)
                return self._post(payload) # Рекурсивная попытка
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка HL: {e}")
            return None
        
    def get_tickers(self):
        """
        Получает список всех активов и их текущие цены.
        """
        print("Скачиваем мету и цены с Hyperliquid...")
        
        # 1. Получаем список монет (Universe)
        meta = self._post({"type": "meta"})
        if not meta: return []

        # 2. Получаем текущие цены (AllMids)
        mids = self._post({"type": "allMids"})
        if not mids: return []

        results = []
        universe = meta.get('universe', [])
        
        for asset in universe:
            symbol = asset['name']
            price = mids.get(symbol)
            
            if price:
                results.append({
                    'symbol': symbol,
                    'price': Decimal(str(price))
                })
        
        return results

    def get_funding_history(self, coin, days=30):
        """
        Получает историю фандинга за N дней.
        """
        end_time_ms = int(time.time() * 1000)
        start_time_ms = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

        payload = {
            "type": "fundingHistory",
            "coin": coin,
            "startTime": start_time_ms,
            "endTime": end_time_ms
        }

        data = self._post(payload)
        if not data:
            return []

        history = []
        for item in data:
            # Преобразуем timestamp из мс в datetime с UTC
            ts = datetime.fromtimestamp(item['time'] / 1000.0, tz=timezone.utc)
            rate = Decimal(str(item['fundingRate']))
            
            # Hyperliquid начисляет фандинг каждый час
            history.append({
                'timestamp': ts,
                'rate': rate,
                'period_hours': 1
            })
            
        return history