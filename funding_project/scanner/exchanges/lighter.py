import time
from decimal import Decimal
from datetime import datetime, timezone
from .base import BaseScanner

class LighterScanner(BaseScanner):
    # CORRECT URL found in your screenshot
    BASE_URL = "https://mainnet.zklighter.elliot.ai/api/v1"

    def __init__(self):
        super().__init__("Lighter")
        self.markets_map = {} # Cache to store symbol -> market_id mapping

    def fetch_tickers(self):
        """
        Fetches active markets using 'assetDetails' and prices from 'orderBookDetails'.
        """
        try:
            assets_data = self._get(f"{self.BASE_URL}/assetDetails")
            
            orders_data = self._get(f"{self.BASE_URL}/orderBookDetails")

            results = []
            
            # Create a lookup map for prices
            price_map = {}
            if orders_data and isinstance(orders_data, list):
                for item in orders_data:
                    # Logic assumes item has 'marketId' or 'symbol' and a price field
                    m_id = item.get('marketId') or item.get('market_id')
                    price = item.get('indexPrice') or item.get('lastPrice') or item.get('bestAsk')
                    if m_id and price:
                        price_map[str(m_id)] = price

            # Process assets
            if assets_data and isinstance(assets_data, list):
                for market in assets_data:
                    # We need to map the internal ID (e.g. 2049) to the Symbol (e.g. "WETH-USDC")
                    market_id = market.get('marketId') or market.get('id')
                    symbol = market.get('symbol') or market.get('name')
                    
                    if not market_id or not symbol: 
                        continue

                    # Save to cache for use in fetch_funding_history
                    self.markets_map[symbol] = market_id
                    
                    # Try to find price
                    price = price_map.get(str(market_id))
                    
                    # Fallback: check if price is inside assetDetails itself
                    if not price:
                        price = market.get('indexPrice') or market.get('lastPrice')

                    if price:
                        results.append({
                            'symbol': symbol,
                            'original_symbol': symbol,
                            'price': Decimal(str(price))
                        })
            
            return results

        except Exception as e:
            print(f"Error fetching Lighter tickers: {e}")
            return []

    def fetch_funding_history(self, original_symbol, lookback_days=30):
        """
        Fetches funding history. 
        Note: Lighter might not have a public 'history' endpoint for funding.
        We will try to fetch the CURRENT rate from assetDetails, which allows 
        your DB to build history over time.
        """
        try:
            # We need the market_id (e.g., 2049) to query specific data
            market_id = self.markets_map.get(original_symbol)
            
            # If we don't have the ID, try to fetch it again
            if not market_id:
                self.fetch_tickers()
                market_id = self.markets_map.get(original_symbol)
                if not market_id:
                    return []

            # STRATEGY 1: Get Current Rate (Most Reliable without specific docs)
            # We re-fetch assetDetails to get the latest funding rate
            assets_data = self._get(f"{self.BASE_URL}/assetDetails")
            
            history = []
            current_time = datetime.now(timezone.utc)
            
            for market in assets_data:
                m_id = market.get('marketId') or market.get('id')
                # Ensure we are looking at the correct market
                if str(m_id) != str(market_id):
                    continue

                # Look for funding rate fields
                # Common names: 'fundingRate', 'currentFundingRate', 'hourlyFundingRate'
                raw_rate = market.get('fundingRate') or market.get('currentFundingRate')
                
                if raw_rate is not None:
                    history.append({
                        'timestamp': current_time,
                        'rate': Decimal(str(raw_rate)),
                        'period_hours': 1 # Lighter usually settles hourly
                    })
                    break
            
            return history

        except Exception as e:
            print(f"Error fetching funding for {original_symbol}: {e}")
            return []