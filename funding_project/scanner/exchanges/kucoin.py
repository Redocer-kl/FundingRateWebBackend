import time
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from .base import BaseScanner

class KucoinScanner(BaseScanner):
    BASE_URL = "https://api-futures.kucoin.com"

    def __init__(self):
        super().__init__("Kucoin")

    def fetch_tickers(self):
        response = self._get(f"{self.BASE_URL}/api/v1/contracts/active")
        if not response or 'data' not in response: return []
        
        results = []
        for item in response['data']:
            original = item['symbol'] 
            
            if not original.endswith('USDTM'): 
                continue

            clean = item['baseCurrency'] 
            
            price = item.get('markPrice')
            
            if price:
                results.append({
                    'symbol': clean,
                    'original_symbol': original,
                    'price': Decimal(str(price))
                })
        return results

    def fetch_funding_history(self, coin, lookback_days=30):
        all_history = []
        
        end_ts = int(datetime.now(timezone.utc).timestamp() * 1000)
        start_ts = int((datetime.now(timezone.utc) - timedelta(days=lookback_days)).timestamp() * 1000)
        
        current_to = end_ts
        
        while True:
            time.sleep(0.15)
            
            params = {
                "symbol": coin,
                "from": start_ts,
                "to": current_to,
                "limit": 100
            }
            
            resp = self._get(f"{self.BASE_URL}/api/v1/contract/funding-rates", params=params)
            
            if not resp or 'data' not in resp: break
            data = resp['data'] # список
            
            if not data: break
            
            batch = []
            min_ts_in_batch = current_to
            
            for item in data:
                ts = item['timepoint']
                min_ts_in_batch = min(min_ts_in_batch, ts)
                
                dt = datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc)
                rate = Decimal(str(item['fundingRate']))
                
                batch.append({
                    'timestamp': dt,
                    'rate': rate,
                    'period_hours': 8 
                })
                
            all_history.extend(batch)
            
            if len(data) < 100:
                break
                
            if min_ts_in_batch <= start_ts:
                break
                
            current_to = min_ts_in_batch - 1
            
        return all_history