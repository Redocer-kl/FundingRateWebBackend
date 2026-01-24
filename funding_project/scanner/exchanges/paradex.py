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

    def fetch_funding_history(self, market, lookback_days=30):
        all_history = []
        start_at = int((datetime.now(tz=timezone.utc) - timedelta(days=lookback_days)).timestamp() * 1000)
        
        url = f"{self.BASE_URL}/v1/funding/data"
        params = {
            'market': market,
            'page_size': 100, 
            'start_at': start_at 
        }

        try:
            data = self._get(url, params=params)
            if not data or not isinstance(data, dict):
                return []
            
            results = data.get('results', [])
            seen_hours = set()

            for item in results:
                raw_ts = int(item.get('created_at', 0))
                ts = datetime.fromtimestamp(raw_ts / 1000.0, tz=timezone.utc)
                
                floored = ts.replace(minute=0, second=0, microsecond=0)
                floored_ts = int(floored.timestamp())

                if floored_ts not in seen_hours:
                    raw_val = Decimal(str(item.get('funding_rate', 0)))
                    rate_1h = raw_val / Decimal('8')

                    all_history.append({
                        'timestamp': floored,
                        'rate': rate_1h,
                        'period_hours': 1
                    })
                    seen_hours.add(floored_ts)

            time.sleep(0.2)

        except Exception as e:
            print(f"Paradex fetch history error for {market}: {e}")

        return all_history