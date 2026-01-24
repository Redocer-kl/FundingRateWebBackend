import requests
import time
from scanner.models import Asset

class CoinGeckoService:
    BASE_URL = "https://api.coingecko.com/api/v3"

    def update_market_data(self):
        print("CoinGecko: Начинаю обновление данных рынка...")
        
        page = 1
        total_updated = 0
        
        while page <= 4: 
            try:
                url = f"{self.BASE_URL}/coins/markets"
                params = {
                    'vs_currency': 'usd',
                    'order': 'market_cap_desc',
                    'per_page': 250,
                    'page': page,
                    'sparkline': 'false'
                }
                
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code == 429:
                    print("CoinGecko Rate Limit (429)")
                    time.sleep(30)
                    continue
                
                if response.status_code != 200:
                    print(f"Ошибка API: {response.status_code}")
                    break

                data = response.json()
                if not data: 
                    break

                for coin in data:
                    cg_symbol = coin['symbol'].upper()
                    count = Asset.objects.filter(symbol=cg_symbol).update(
                        market_cap=coin.get('market_cap'),
                        volume_24h=coin.get('total_volume'),
                        image_url=coin.get('image'),
                        coingecko_id=coin.get('id')
                    )
                    total_updated += count

                print(f"CoinGecko Страница {page} обработана.")
                page += 1
                
                time.sleep(10) 

            except Exception as e:
                print(f"Ошибка CoinGecko: {e}")
                break
        
        return f"Успешно обновлено {total_updated} активов"