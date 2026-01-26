import logging
import cloudscraper
from abc import ABC, abstractmethod
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential, retry_if_exception_type
import urllib3
from urllib.parse import urlparse
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

class BaseScanner(ABC):
    def __init__(self, exchange_name):
        self.name = exchange_name
        
        self.session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }

        base_url = getattr(self, 'BASE_URL', None)
        if base_url:
            parsed_url = urlparse(base_url)
            origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
            headers.update({
                "Origin": origin,
                "Referer": f"{origin}/"
            })
        
        self.session.headers.update(headers)


    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2),
           retry=retry_if_exception_type((requests.RequestException, Exception)), reraise=True)
    def _get(self, url, params=None):
        try:
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 429:
                logger.warning(f"{self.name} 429 rate limit for {url}")
            
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
            logger.warning(f"{self.name} _get HTTPError {status} for {url}. Body: {text}")
            raise
        except Exception as e:
            logger.warning(f"{self.name} _get Exception for {url}: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2),
           retry=retry_if_exception_type((requests.RequestException, Exception)), reraise=True)
    def _post(self, url, data=None, json_data=None, params=None, headers=None):
        try:
            # cloudscraper.session.post принимает json=... и data=...
            resp = self.session.post(url, params=params, data=data, json=json_data, headers=headers, timeout=15)

            if resp.status_code == 429:
                logger.warning(f"{self.name} 429 rate limit for {url}")

            resp.raise_for_status()

            try:
                return resp.json()
            except ValueError:
                return resp.text
        except requests.HTTPError as e:
            resp = getattr(e, 'response', None)
            status = resp.status_code if resp is not None else 'N/A'
            text = ''
            try:
                text = (resp.text[:1000] if resp is not None and resp.text else str(e))
            except Exception:
                text = str(e)
            logger.warning(f"{self.name} _post HTTPError {status} for {url}. Body: {text}")
            raise
        except Exception as e:
            logger.warning(f"{self.name} _post Exception for {url}: {e}")
            raise
