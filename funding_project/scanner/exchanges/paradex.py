import time
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from .base import BaseScanner

class ParadexScanner(BaseScanner):
    BASE_URL = "https://api.prod.paradex.trade"
    SAMPLE_INTERVAL_MINUTES = 60

    def __init__(self):
        super().__init__("Paradex")

    def _normalize_symbol(self, raw: str) -> str:
        if not raw: return raw
        return raw.split('-')[0].upper()

    def fetch_tickers(self):
        url = f"{self.BASE_URL}/v1/markets/summary"
        try:
            data = self._get(url, params={'market': 'ALL'})
            results = data.get('results', []) if isinstance(data, dict) else data
            out = []
            for r in results:
                symbol = r.get('symbol', '')
                if not symbol.endswith('-PERP'): continue
                price = r.get('mark_price') or r.get('last_traded_price')
                if price:
                    out.append({
                        'symbol': self._normalize_symbol(symbol),
                        'original_symbol': symbol,
                        'price': Decimal(str(price))
                    })
            return out
        except Exception as e:
            print(f"Paradex fetch_tickers error: {e}")
            return []

    def fetch_funding_history(self, market, lookback_days=30, sample_minutes=60):
        all_history = []
        now = datetime.now(tz=timezone.utc)
        start_dt = now - timedelta(days=lookback_days)
        start_ts_ms = int(start_dt.timestamp() * 1000)
        
        url = f"{self.BASE_URL}/v1/funding/data"
        params = {
            'market': market,
            'page_size': 100  # Максимально допустимый размер
        }
        
        seen_floored = set()
        cursor = None
        # Увеличиваем лимит итераций, чтобы уйти глубже в историю
        for _ in range(300): 
            if cursor:
                params['cursor'] = cursor

            try:
                data = self._get(url, params=params)
                if not data or not isinstance(data, dict): break
                
                results = data.get('results', [])
                if not results: break

                for item in results:
                    raw_ts = int(item.get('created_at', 0))
                    # Если дошли до данных старее, чем нам нужно — стоп
                    if raw_ts < start_ts_ms:
                        return all_history 

                    ts = datetime.fromtimestamp(raw_ts / 1000.0, tz=timezone.utc)
                    # Округляем до часа
                    floored = ts.replace(minute=0, second=0, microsecond=0)
                    floored_ts = int(floored.timestamp())

                    if floored_ts not in seen_floored:
                        raw_val = Decimal(str(item.get('funding_rate', 0)))
                        # Конвертация в 1h ставку (Paradex обычно дает 8h или абсолют)
                        rate_1h = raw_val / Decimal('8')
                        
                        all_history.append({
                            'timestamp': floored,
                            'rate': rate_1h,
                            'period_hours': 1
                        })
                        seen_floored.add(floored_ts)

                cursor = data.get('next')
                if not cursor: break
                
                time.sleep(0.2) # Пауза, чтобы Windows/Paradex не обрывали соединение
            except Exception as e:
                print(f"Loop error for {market}: {e}")
                break

        return all_history