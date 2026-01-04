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

    def fetch_funding_history(self, market, lookback_days=30, sample_minutes=None):
        all_history = []
        now = datetime.now(tz=timezone.utc)
        
        # Вычисляем общее количество прыжков (3 раза в день * кол-во дней)
        # 30 дней * 3 = 90 запросов на одну монету
        total_jumps = lookback_days * 3
        hours_step = 8 

        seen_timestamps = set()

        for jump in range(total_jumps):
            # Вычисляем время для текущего прыжка (идем назад от 'now')
            target_date = now - timedelta(hours=jump * hours_step)
            end_at_ms = int(target_date.timestamp() * 1000)
            
            url = f"{self.BASE_URL}/v1/funding/data"
            params = {
                'market': market,
                'page_size': 1,  # Нам нужна только одна ближайшая запись к этому времени
                'end_at': end_at_ms
            }

            try:
                data = self._get(url, params=params)
                if not data or not isinstance(data, dict):
                    continue
                
                results = data.get('results', [])
                if not results:
                    # Если данных нет совсем глубоко в истории, можно прервать цикл раньше
                    if jump > 10: # Небольшой запас
                        break
                    continue

                item = results[0]
                raw_ts = int(item.get('created_at', 0))
                ts = datetime.fromtimestamp(raw_ts / 1000.0, tz=timezone.utc)
                
                # Округляем до часа для базы данных
                floored = ts.replace(minute=0, second=0, microsecond=0)
                floored_ts = int(floored.timestamp())

                # Проверяем, не сохраняли ли мы уже эту точку (чтобы не дублировать)
                if floored_ts not in seen_timestamps:
                    raw_val = Decimal(str(item.get('funding_rate', 0)))
                    # Paradex ставка за 8ч, делим на 8 для получения часовой ставки (для APR)
                    rate_1h = raw_val / Decimal('8')

                    all_history.append({
                        'timestamp': floored,
                        'rate': rate_1h,
                        'period_hours': 1
                    })
                    seen_timestamps.add(floored_ts)
                
                # Логируем раз в день (каждый 3-й прыжок), чтобы не спамить в консоль
                if jump % 3 == 0:
                    print(f"Paradex [{market}]: Сбор данных за {ts.strftime('%Y-%m-%d %H:%M')}")
                
                # Небольшая пауза, чтобы избежать Rate Limit (особенно важно при 90 запросах на монету)
                time.sleep(0.05)

            except Exception as e:
                print(f"Paradex jump error at {target_date}: {e}")
                continue

        # Сортируем от старых к новым перед возвратом
        all_history.sort(key=lambda x: x['timestamp'])
        return all_history