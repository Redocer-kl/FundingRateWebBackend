import time
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from .base import BaseScanner

class BinanceScanner(BaseScanner):
    BASE_URL = "https://fapi.binance.com"

    def __init__(self):
        super().__init__("Binance")

    def fetch_tickers(self):
        data = self._get(f"{self.BASE_URL}/fapi/v1/premiumIndex")
        if not data: return []

        results = []
        for item in data:
            symbol = item['symbol']
            if "_" in symbol: 
                continue

            price = item.get('markPrice')
            
            clean_symbol = symbol
            if symbol.endswith('USDT'):
                clean_symbol = symbol[:-4]
            elif symbol.endswith('BUSD'):
                clean_symbol = symbol[:-4]

            results.append({
                'symbol': clean_symbol,
                'original_symbol': symbol,
                'price': Decimal(str(price))
            })
        return results

    def fetch_funding_history(self, coin, lookback_days=30):
        all_history = []
        start_dt = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        start_ts = int(start_dt.timestamp() * 1000)
        
        while True:
            time.sleep(0.1) 
            
            params = {
                "symbol": coin,
                "startTime": start_ts,
                "limit": 1000 
            }
            
            data = self._get(f"{self.BASE_URL}/fapi/v1/fundingRate", params=params)
            if not data:
                break
                
            batch = []
            last_ts = start_ts
            
            for item in data:
                ts_ms = item['fundingTime']
                last_ts = ts_ms
                
                dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
                rate = Decimal(str(item['fundingRate']))
                
                batch.append({
                    'timestamp': dt,
                    'rate': rate,
                    'period_hours': 8 
                })
            
            all_history.extend(batch)
            
            if len(data) < 1000:
                break
            
            start_ts = last_ts + 1
            
        return all_history