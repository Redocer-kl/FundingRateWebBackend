import time
import logging
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from .base import BaseScanner

logger = logging.getLogger(__name__)

class ApexScanner(BaseScanner):
    BASE_URL = "https://pro.apex.exchange"

    def __init__(self):
        super().__init__("Apex")

    def fetch_tickers(self):
        url = f"{self.BASE_URL}/api/v1/symbols"
        response = self._get(url)
        
        results = []
        if isinstance(response, dict) and 'data' in response:
            items = response['data'].get('perpetualContract', [])
            for item in items:
                symbol = item.get('symbol')
                # Цены в этом эндпоинте нет, ставим заглушку 0.0
                if symbol:
                    clean = symbol.replace('-USDT', '').replace('USDT', '').replace('-USDC', '').replace('USDC', '')
                    results.append({
                        'symbol': clean,
                        'original_symbol': symbol,
                        'price': Decimal('0.0')
                    })
        return results

    def fetch_funding_history(self, symbol, lookback_days=1):
        url = f"{self.BASE_URL}/api/v1/history/funding-rate"
        
        now = datetime.now(timezone.utc)
        params = {
            "symbol": symbol,
            "start_time": int((now - timedelta(days=lookback_days)).timestamp()),
            "end_time": int(now.timestamp())
        }
        
        try:
            resp = self._get(url, params=params)
            
            if not resp or not isinstance(resp, dict) or resp.get('code') != 0:
                return []
            
            data_content = resp.get('data', [])
            records = data_content if isinstance(data_content, list) else data_content.get('rows', [])
            
            results = []
            for item in records:
                rate = item.get('fundingRate')
                ts = item.get('timestamp')
                
                if rate is not None and ts:
                    ts_f = float(ts)
                    if ts_f > 10**11: ts_f /= 1000
                        
                    results.append({
                        'timestamp': datetime.fromtimestamp(ts_f, tz=timezone.utc),
                        'rate': Decimal(str(rate)),
                        'period_hours': 1
                    })
            return results
        except Exception:
            return []