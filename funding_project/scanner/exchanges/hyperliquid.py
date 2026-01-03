import time
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from .base import BaseScanner

class HyperliquidScanner(BaseScanner):
    BASE_URL = "https://api.hyperliquid.xyz/info"

    def __init__(self):
        super().__init__("Hyperliquid")

    def fetch_tickers(self):
        # 1. Получаем Universe
        meta = self._post(self.BASE_URL, json_data={"type": "meta"})
        # 2. Получаем цены
        mids = self._post(self.BASE_URL, json_data={"type": "allMids"})
        
        if not meta or not mids: return []

        results = []
        universe = meta.get('universe', [])
        
        for asset in universe:
            original = asset['name'] # Например "BTC" или "1000PEPE"
            
            # Нормализация для Hyperliquid (убираем "1000" для мемкоинов, если нужно)
            clean_symbol = original
            if original.startswith('1000'):
                clean_symbol = original[4:]
            
            price = mids.get(original)
            if price:
                results.append({
                    'symbol': clean_symbol,
                    'original_symbol': original, # HL требует точное имя (н-р 1000PEPE)
                    'price': Decimal(str(price))
                })
        return results

    def fetch_funding_history(self, coin, lookback_days=30):
        all_history = []
        # Определяем точку старта (30 дней назад)
        target_start_ms = int((datetime.now() - timedelta(days=lookback_days)).timestamp() * 1000)
        
        # Текущий указатель времени, который будем сдвигать вперед
        current_start_ms = target_start_ms

        while True:
            # Увеличил паузу, так как HL очень чувствителен к лимитам (видно по твоим логам)
            time.sleep(0.5) 
            
            payload = {
                "type": "fundingHistory",
                "coin": coin,
                "startTime": current_start_ms
            }
            
            try:
                data = self._post(self.BASE_URL, json_data=payload)
                if not data or not isinstance(data, list):
                    break

                batch = []
                last_ts_in_batch = current_start_ms
                
                for item in data:
                    # Сохраняем время последней записи, чтобы в следующем цикле начать С НЕГО
                    last_ts_in_batch = item['time']
                    
                    ts = datetime.fromtimestamp(item['time'] / 1000.0, tz=timezone.utc)
                    batch.append({
                        'timestamp': ts,
                        'rate': Decimal(str(item['fundingRate'])),
                        'period_hours': 1
                    })
                
                all_history.extend(batch)
                
                # Если мы получили меньше 500 записей, значит мы дошли до "сейчас"
                if len(data) < 500:
                    break
                
                # Если получили ровно 500, значит впереди есть еще данные.
                # Сдвигаем время старта на 1 мс вперед от последней полученной записи
                if last_ts_in_batch <= current_start_ms:
                    # Защита от бесконечного цикла, если API отдает одно и то же время
                    break
                    
                current_start_ms = last_ts_in_batch + 1

            except Exception as e:
                print(f"Ошибка HL для {coin}: {e}")
                break
                
        return all_history