from celery import shared_task
from .models import Exchange, Ticker, FundingRate
from django.utils import timezone

# Импортируем сканеры
from .exchanges.bitget import BitgetScanner
from .exchanges.hyperliquid import HyperliquidScanner
from .exchanges.apex import ApexScanner
from .exchanges.paradex import ParadexScanner
from .exchanges.edgex import EdgeXScanner
from .exchanges.lighter import LighterScanner
from .exchanges.extended import ExtendedScanner

# Реестр сканеров
SCANNERS = {
    'Bitget': BitgetScanner,
    'Hyperliquid': HyperliquidScanner,
    'Apex': ApexScanner,
    'Paradex': ParadexScanner,
    'EdgeX':  EdgeXScanner,
    'Lighter': LighterScanner,
    'Extended': ExtendedScanner
}

@shared_task
def scan_exchange_task(exchange_name):
    """
    Универсальная задача сканирования биржи.
    Принимает имя биржи (ключ в SCANNERS).
    """
    if exchange_name not in SCANNERS:
        return f"Сканер для {exchange_name} не найден"
    
    # Инициализация
    ScannerClass = SCANNERS[exchange_name]
    scanner = ScannerClass() # Если нужны API ключи, их можно брать из settings
    
    print(f"Запуск сканирования: {exchange_name}")
    
    # 1. Получаем тикеры
    market_data = scanner.fetch_tickers()
    if not market_data:
        return f"{exchange_name}: Нет данных тикеров"
    
    # Создаем/получаем биржу в БД
    exchange_obj, _ = Exchange.objects.get_or_create(name=exchange_name)
    
    processed_count = 0
    
    # Ограничиваем список для теста, если нужно (например, первые 50)
    # market_data = market_data[:50] 
    
    for item in market_data:
        # Сохраняем тикер
        ticker, _ = Ticker.objects.update_or_create(
            exchange=exchange_obj,
            symbol=item['symbol'],
            defaults={'last_price': item['price']}
        )
        
        # Определяем, сколько истории качать
        last_entry = FundingRate.objects.filter(ticker=ticker).order_by('-timestamp').first()
        
        # Логика "lookback" должна быть внутри метода fetch_funding_history или передаваться
        # В BaseScanner мы договорились передавать lookback_days
        days_to_fetch = 1 if last_entry else 30
        
        # Скачиваем историю
        # Важно передавать original_symbol, так как в API может быть "BTC-USD-PERP", а у нас в БД просто "BTC"
        history = scanner.fetch_funding_history(item.get('original_symbol', item['symbol']), lookback_days=days_to_fetch)
        
        new_records = []
        for row in history:
            # Проверка на дубли
            if not FundingRate.objects.filter(ticker=ticker, timestamp=row['timestamp']).exists():
                # Расчет APR
                # Формула: rate * (24 / period_hours) * 365 * 100
                period = row.get('period_hours', 8) # По дефолту 8, если сканер не вернул
                if period == 0: period = 1 # Защита от деления на ноль
                
                daily_rate = row['rate'] * (24 // period) # Упрощенно
                apr_val = daily_rate * 365 * 100
                
                new_records.append(FundingRate(
                    ticker=ticker,
                    timestamp=row['timestamp'],
                    rate=row['rate'],
                    period_hours=period,
                    apr=apr_val
                ))
        
        if new_records:
            FundingRate.objects.bulk_create(new_records)
            processed_count += len(new_records)
            
    return f"{exchange_name}: Обработано записей {processed_count}"