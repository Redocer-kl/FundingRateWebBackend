from decimal import Decimal
from datetime import datetime, timezone
from .base import BaseScanner
import logging

logger = logging.getLogger(__name__)

class CoinexScanner(BaseScanner):
    BASE_URL = "https://api.coinex.com/v2"

    def __init__(self):
        super().__init__("CoinEx")

    def fetch_tickers(self):
        url = f"{self.BASE_URL}/spot/ticker"
        response = self._get(url)
        
        if not response or response.get('code') != 0:
            logger.error(f"CoinEx v2 error: {response}")
            return []
            
        data_list = response.get('data', [])
        results = []
        
        for item in data_list:
            market = item.get('market')
            if market and market.endswith('USDT'):
                price = item.get('last')
                if price:
                    results.append({
                        'symbol': market.replace('USDT', ''),
                        'original_symbol': market,
                        'price': Decimal(str(price))
                    })
        return results

    def fetch_funding_history(self, symbol, lookback_days=1):
        url = f"{self.BASE_URL}/futures/funding-rate-history"
        
        params = {
            "market": symbol,
            "limit": 50
        }
        
        try:
            response = self._get(url, params=params)
            
            if not response or response.get('code') != 0:
                return []
                
            records = response.get('data', [])
            
            if isinstance(records, dict):
                records = records.get('list', [])

            if not records:
                return []

            results = []
            for rec in records:
                rate = rec.get('actual_funding_rate')
                ts = rec.get('funding_time')
                
                if rate is not None and ts:
                    ts_seconds = float(ts) / 1000
                    
                    results.append({
                        'timestamp': datetime.fromtimestamp(ts_seconds, tz=timezone.utc),
                        'rate': Decimal(str(rate)),
                        'period_hours': 8
                    })
            return results
        except Exception as e:
            logger.error(f"CoinEx history parsing failed for {symbol}: {e}")
            return []