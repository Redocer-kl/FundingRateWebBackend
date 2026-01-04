import time
import re
import logging
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from .base import BaseScanner

logger = logging.getLogger(__name__)

class EdgeXScanner(BaseScanner):
    BASE_URL = "https://pro.edgex.exchange"

    # Постфиксы, которые нужно убрать из имени
    _POSTFIX_RE = re.compile(r'(?:[_\-/\s]?(?:USD|USDT|USDC|TUSD|PERP|PERPETUAL|PERPS))+$', re.IGNORECASE)

    def __init__(self):
        super().__init__("EdgeX")

    def _clean_symbol(self, contract_name: str) -> str:
        if not contract_name:
            return contract_name
        s = contract_name.strip()
        s = re.sub(self._POSTFIX_RE, '', s).strip()
        for sep in ['/', '-', '_', ' ']:
            if sep in s:
                parts = s.split(sep)
                if parts and re.match(r'^[A-Za-z0-9]+$', parts[0]):
                    return parts[0]
        return s

    def _is_html_challenge(self, resp):
        """
        Detect Cloudflare / HTML challenge. _get may return a string (text/html) on that case.
        """
        if isinstance(resp, str):
            snippet = resp[:300].lower()
            if '<!doctype' in snippet or 'just a moment' in snippet or 'cf_chl_opt' in snippet:
                return True
        return False

    def fetch_tickers(self):
        """
        Возвращает список словарей:
        {'symbol': clean_symbol, 'original_symbol': contractId, 'price': Decimal(...)}
        Стратегия:
          - GET meta/getMetaData
          - GET funding/getLatestFundingRate (bulk) -> взять indexPrice/oraclePrice
          - для контрактов, которых нет в bulk-ответе — пропустить (чтобы не делать тысячи запросов)
        """
        try:
            meta = self._get(f"{self.BASE_URL}/api/v1/public/meta/getMetaData")
        except Exception as e:
            logger.warning(f"EdgeX getMetaData failed: {e}")
            return []

        meta_data = meta.get('data') if isinstance(meta, dict) else None
        if not meta_data:
            logger.debug("EdgeX meta has no data")
            return []

        contract_list = meta_data.get('contractList') or []
        if not contract_list:
            logger.debug("EdgeX contractList empty")
            return []

        # Попробуем bulk-ответ по funding latest (возвращает список funding info с indexPrice/oraclePrice)
        price_map = {}
        try:
            time.sleep(0.08)
            latest = self._get(f"{self.BASE_URL}/api/v1/public/funding/getLatestFundingRate")
            if self._is_html_challenge(latest):
                logger.warning("EdgeX fetch_tickers: getLatestFundingRate returned HTML (Cloudflare). Aborting bulk price fetch.")
                latest = None
        except Exception as e:
            logger.debug(f"EdgeX getLatestFundingRate failed: {e}")
            latest = None

        if latest and isinstance(latest, dict):
            # docs show response: { "code":"SUCCESS", "data": [ {...}, {...} ] }
            data = latest.get('data')
            if isinstance(data, list):
                for item in data:
                    try:
                        cid = str(item.get('contractId') or item.get('contractIdStr') or '')
                        price_raw = item.get('indexPrice') or item.get('oraclePrice') or item.get('price')
                        if cid and price_raw not in (None, ''):
                            price_map[cid] = Decimal(str(price_raw))
                    except Exception:
                        continue

        results = []
        # Если bulk дал мало данных, всё равно используем те что есть, но не делаем per-contract GET
        for c in contract_list:
            contract_id = str(c.get('contractId') or c.get('contractIdStr') or '')
            contract_name = c.get('contractName') or c.get('contractNameCn') or c.get('symbol') or ''
            if not contract_id:
                continue

            clean_symbol = self._clean_symbol(contract_name)

            price = price_map.get(contract_id)
            if price is None:
                # не пытаться per-contract, т.к. вызывает 429; логируем и пропускаем
                logger.debug(f"EdgeX fetch_tickers: no bulk price for {contract_id} ({clean_symbol}), skipping to avoid rate limit.")
                continue

            results.append({
                'symbol': clean_symbol,
                'original_symbol': contract_id,
                'price': price
            })

        if not results:
            logger.warning("EdgeX fetch_tickers: no tickers returned (maybe Cloudflare/429).")

        return results

    def fetch_funding_history(self, original_symbol, lookback_days=30):
        """
        Получаем историю фандинга для contractId (original_symbol).
        Пагинация через offsetData.
        Устойчивость к 429: экспоненциальный backoff (ограниченный), детект HTML -> abort.
        """
        contract_id = str(original_symbol)
        all_history = []

        now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
        start_ms = int((datetime.now(tz=timezone.utc) - timedelta(days=lookback_days)).timestamp() * 1000)

        offset = ''
        page_size = 100
        page = 0
        max_pages = 1000

        # backoff base
        backoff_base = 0.5

        while True:
            page += 1
            if page > max_pages:
                logger.warning(f"EdgeX fetch_funding_history: max_pages reached for {contract_id}")
                break

            params = {'contractId': contract_id, 'size': str(page_size)}
            if offset:
                params['offsetData'] = offset
            else:
                params['filterBeginTimeInclusive'] = str(start_ms)
                params['filterEndTimeExclusive'] = str(now_ms)

            try:
                resp = self._get(f"{self.BASE_URL}/api/v1/public/funding/getFundingRatePage", params=params)
            except Exception as e:
                # Если 429 захвачен в _get — там уже логируется. Сделаем экспоненциальную паузу и пробуем ещё N раз.
                logger.warning(f"EdgeX getFundingRatePage request error for {contract_id}: {e}")
                # Backoff and try a few times
                retry_attempts = 0
                max_retries = 4
                waited = 0
                success = False
                while retry_attempts < max_retries:
                    retry_attempts += 1
                    sleep_t = backoff_base * (2 ** (retry_attempts - 1))
                    waited += sleep_t
                    logger.debug(f"EdgeX funding backoff for {contract_id}: sleeping {sleep_t}s (attempt {retry_attempts})")
                    time.sleep(sleep_t)
                    try:
                        resp = self._get(f"{self.BASE_URL}/api/v1/public/funding/getFundingRatePage", params=params)
                        success = True
                        break
                    except Exception as e2:
                        logger.debug(f"EdgeX funding retry {retry_attempts} failed for {contract_id}: {e2}")
                        continue
                if not success:
                    logger.warning(f"EdgeX fetch_funding_history: failed after retries for {contract_id}; aborting history fetch.")
                    break

            # Если HTML / Cloudflare
            if self._is_html_challenge(resp):
                logger.warning(f"EdgeX getFundingRatePage for {contract_id} returned HTML (Cloudflare). Aborting history fetch.")
                break

            # ожидание структуры: {'code': 'SUCCESS', 'data': {'dataList': [...], 'nextPageOffsetData': '...'}}
            page_data = resp.get('data') if isinstance(resp, dict) else None
            if not page_data:
                logger.debug(f"EdgeX funding page no data for {contract_id}; resp keys: {list(resp.keys()) if isinstance(resp, dict) else 'n/a'}")
                break

            data_list = page_data.get('dataList') or []
            if not data_list:
                break

            last_ts = None
            for item in data_list:
                ts_ms = item.get('fundingTimestamp') or item.get('fundingTime')
                if not ts_ms:
                    continue
                try:
                    ts = datetime.fromtimestamp(int(ts_ms) / 1000.0, tz=timezone.utc)
                except Exception:
                    continue

                rate_raw = item.get('fundingRate') or item.get('rate')
                try:
                    rate = Decimal(str(rate_raw))
                except Exception:
                    continue

                interval_min = item.get('fundingRateIntervalMin')
                try:
                    period_hours = int(int(interval_min) / 60) if interval_min is not None else 8
                    if period_hours == 0:
                        period_hours = 1
                except Exception:
                    period_hours = 8

                all_history.append({
                    'timestamp': ts,
                    'rate': rate,
                    'period_hours': period_hours
                })

                try:
                    last_ts = int(ts_ms)
                except Exception:
                    pass

            next_offset = page_data.get('nextPageOffsetData')
            if not next_offset:
                break

            if next_offset == offset:
                break

            offset = next_offset
            # small friendly pause between pages
            time.sleep(0.18)

        # Отсортируем по времени (старые -> новые)
        all_history.sort(key=lambda x: x['timestamp'])
        return all_history
