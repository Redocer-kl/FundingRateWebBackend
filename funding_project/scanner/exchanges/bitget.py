import time
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from .base import BaseScanner # Обязательно наследуемся от BaseScanner

class BitgetScanner(BaseScanner): # Наследуемся
    TICKERS_URL = "https://api.bitget.com/api/v2/mix/market/tickers"
    FUNDING_URL = "https://api.bitget.com/api/v2/mix/market/history-fund-rate"

    def __init__(self):
        super().__init__("Bitget")

    def fetch_tickers(self):
        params = {"productType": "USDT-FUTURES"}
        try:
            resp = self._get(self.TICKERS_URL, params=params)
            data = resp.get("data")
            if data is None: return []
            
            results = []
            for item in data:
                original = item['symbol']  # Например, "BTCUSDT"
                
                # НОРМАЛИЗАЦИЯ: убираем USDT в конце
                # Если символ "BTCUSDT", останется "BTC"
                clean_symbol = original
                if original.endswith('USDT'):
                    clean_symbol = original[:-4]
                elif original.endswith('USDT_SUMP'): # На всякий случай для экзотики
                    clean_symbol = original.replace('USDT_SUMP', '')

                results.append({
                    'symbol': clean_symbol,          # Для нашей базы (группировки)
                    'original_symbol': original,     # Для будущих запросов к API
                    'price': Decimal(str(item['lastPr']))
                })
            return results
        except Exception as e:
            print(f"Ошибка получения тикеров Bitget: {e}")
            return []

    def fetch_funding_history(self, original_symbol, lookback_days=30):
        all_history = []
        now = datetime.now(tz=timezone.utc)
        limit_ts = int((now - timedelta(days=lookback_days)).timestamp() * 1000)
        
        # Начинаем с текущего времени
        current_end_time = int(now.timestamp() * 1000)
        seen_timestamps = set()

        # Делаем до 15 итераций (чтобы точно покрыть 30 дней пачками по 20)
        for i in range(15):
            params = {
                "symbol": original_symbol,
                "productType": "USDT-FUTURES",
                "limit": 100, # Просим 100, но Bitget может упрямо отдавать 20
                "endTime": current_end_time
            }

            try:
                resp = self._get(self.FUNDING_URL, params=params)
                data = resp.get("data") or []
                
                if not data:
                    break

                # Важно: Bitget отдает список, где data[0] — самая свежая запись, 
                # а data[-1] — самая старая в этой пачке.
                for item in data:
                    f_time = int(item['fundingTime'])
                    
                    if f_time < limit_ts:
                        continue

                    ts = datetime.fromtimestamp(f_time / 1000.0, tz=timezone.utc)
                    floored = ts.replace(minute=0, second=0, microsecond=0)
                    ts_key = int(floored.timestamp())

                    if ts_key not in seen_timestamps:
                        all_history.append({
                            'timestamp': floored,
                            'rate': Decimal(str(item['fundingRate'])),
                            'period_hours': 8 
                        })
                        seen_timestamps.add(ts_key)

                # Берем время САМОГО СТАРОГО элемента в пачке (последний в списке)
                oldest_in_batch = int(data[-1]['fundingTime'])
                
                # Если мы не продвинулись во времени (защита от зацикливания)
                if oldest_in_batch >= current_end_time:
                    break
                
                # Обновляем точку отсчета для следующего запроса
                current_end_time = oldest_in_batch
                
                # Если мы уже зашли за предел 30 дней, выходим
                if oldest_in_batch < limit_ts:
                    break
                
                # Пауза, чтобы не поймать бан
                time.sleep(0.1)

            except Exception as e:
                print(f"Bitget pagination error: {e}")
                break

        print(f"Bitget [{original_symbol}]: Собрано {len(all_history)} записей (глубина ~{len(all_history)//3} дн.)")
        all_history.sort(key=lambda x: x['timestamp'])
        return all_history