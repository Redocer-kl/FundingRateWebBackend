import time
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from .base import BaseScanner 

class BitgetScanner(BaseScanner): #
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
                original = item['symbol']  
                
                clean_symbol = original
                if original.endswith('USDT'):
                    clean_symbol = original[:-4]
                elif original.endswith('USDT_SUMP'): 
                    clean_symbol = original.replace('USDT_SUMP', '')

                results.append({
                    'symbol': clean_symbol,          
                    'original_symbol': original,     
                    'price': Decimal(str(item['lastPr']))
                })
            return results
        except Exception as e:
            print(f"Ошибка получения тикеров Bitget: {e}")
            return []

    def fetch_funding_history(self, original_symbol, lookback_days=30):
        all_history = []
        now = datetime.now(tz=timezone.utc)
        limit_ts = int((now - timedelta(days=lookback_days)).timestamp() * 1000)
        
        current_end_time = int(now.timestamp() * 1000)
        seen_timestamps = set()

        for i in range(15):
            params = {
                "symbol": original_symbol,
                "productType": "USDT-FUTURES",
                "limit": 100,
                "endTime": current_end_time
            }

            try:
                resp = self._get(self.FUNDING_URL, params=params)
                data = resp.get("data") or []
                
                if not data:
                    break

                for item in data:
                    f_time = int(item['fundingTime'])
                    
                    if f_time < limit_ts:
                        continue

                    ts = datetime.fromtimestamp(f_time / 1000.0, tz=timezone.utc)
                    floored = ts.replace(minute=0, second=0, microsecond=0)
                    ts_key = int(floored.timestamp())

                    if ts_key not in seen_timestamps:
                        all_history.append({
                            'timestamp': floored,
                            'rate': Decimal(str(item['fundingRate'])),
                            'period_hours': 8 
                        })
                        seen_timestamps.add(ts_key)

                oldest_in_batch = int(data[-1]['fundingTime'])
                
                if oldest_in_batch >= current_end_time:
                    break
                
                current_end_time = oldest_in_batch
                
                if oldest_in_batch < limit_ts:
                    break
                
                time.sleep(0.1)

            except Exception as e:
                print(f"Bitget pagination error: {e}")
                break

        print(f"Bitget [{original_symbol}]: Собрано {len(all_history)} записей (глубина ~{len(all_history)//3} дн.)")
        all_history.sort(key=lambda x: x['timestamp'])
        return all_history