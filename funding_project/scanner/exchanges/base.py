# base.py
import logging
import requests
from abc import ABC, abstractmethod
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential, retry_if_exception_type
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

class BaseScanner(ABC):
    def __init__(self, exchange_name):
        self.name = exchange_name
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://app.paradex.trade/",
            "Origin": "https://app.paradex.trade/",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        })

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2),
           retry=retry_if_exception_type(requests.RequestException), reraise=True)
    def _get(self, url, params=None):
        try:
            response = self.session.get(url, params=params, timeout=15, verify=False)
            # явная обработка 429, чтобы мы могли логировать и дать Tenacity повторить
            if response.status_code == 429:
                # исправлено: используем self._get.__name__ вместо необъявленного _get
                logger.warning(f"{self.name} {self._get.__name__}: 429 rate limit for {url} params={params}")
            response.raise_for_status()
            try:
                return response.json()
            except ValueError:
                # если не JSON — возвращаем текст (для дебага)
                return response.text
        except requests.HTTPError as e:
            resp = getattr(e, 'response', None)
            status = resp.status_code if resp is not None else 'N/A'
            text = ''
            try:
                text = (resp.text[:1000] if resp is not None and resp.text else str(e))
            except Exception:
                text = str(e)
            logger.warning(f"{self.name} _get HTTPError {status} for {url} params={params} body='{text}'")
            raise
        except requests.RequestException as e:
            logger.warning(f"{self.name} _get RequestException for {url} params={params}: {e}")
            raise

    @retry(stop=stop_after_attempt(5),
           wait=wait_exponential(multiplier=1, min=2, max=10),
           retry=retry_if_exception_type(requests.RequestException),
           reraise=True)
    def _post(self, url, json_data=None):
        try:
            response = self.session.post(url, json=json_data, timeout=15, verify=False)
            if response.status_code == 429:
                logger.warning(f"Rate limit hit on {self.name} POST {url} json={json_data}")
            response.raise_for_status()
            try:
                return response.json()
            except ValueError:
                return response.text
        except requests.HTTPError as e:
            resp = getattr(e, 'response', None)
            status = resp.status_code if resp is not None else 'N/A'
            text = ''
            try:
                text = (resp.text[:1000] if resp is not None and resp.text else str(e))
            except Exception:
                text = str(e)
            logger.warning(f"{self.name} _post HTTPError {status} for {url} json={json_data} body='{text}'")
            raise
        except requests.RequestException as e:
            logger.warning(f"{self.name} _post RequestException for {url} json={json_data}: {e}")
            raise
