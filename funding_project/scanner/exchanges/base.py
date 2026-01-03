import logging
from abc import ABC, abstractmethod
from decimal import Decimal
from datetime import datetime
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)

class BaseScanner(ABC):
    def __init__(self, exchange_name):
        self.name = exchange_name
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "FundingScanner/1.0",
            "Accept": "application/json"
        })

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _get(self, url, params=None):
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _post(self, url, json_data=None):
        response = self.session.post(url, json=json_data, timeout=10)
        response.raise_for_status()
        return response.json()

    @abstractmethod
    def fetch_tickers(self):
        """Возвращает список тикеров: [{'symbol': 'BTC', 'price': 10000, 'original_symbol': 'BTC-USD'}]"""
        pass

    @abstractmethod
    def fetch_funding_history(self, original_symbol, lookback_days=30):
        """
        Возвращает историю фандинга.
        Формат: [{'timestamp': datetime, 'rate': Decimal, 'period_hours': int}]
        """
        pass