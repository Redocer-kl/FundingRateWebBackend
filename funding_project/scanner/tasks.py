from celery import shared_task
from django.utils import timezone
from .models import Exchange, Ticker, FundingRate
from .exchanges.hyperliquid import HyperliquidScanner
from .exchanges.bitget import BitgetScanner
from decimal import Decimal

@shared_task
def scan_hyperliquid_task():
    """
    Эта функция будет запускаться Celery каждые 10 минут.
    """
    print(f"[{timezone.now()}] Старт фоновой задачи: Hyperliquid")
    
    # 1. Инициализация
    exchange, _ = Exchange.objects.get_or_create(name="Hyperliquid")
    scanner = HyperliquidScanner()
    
    # 2. Получение тикеров
    try:
        market_data = scanner.get_tickers()
    except Exception as e:
        print(f"Ошибка получения тикеров: {e}")
        return "Error fetching tickers"

    if not market_data:
        return "No data received"

    # 3. Обработка
    processed_count = 0
    for item in market_data:
        symbol = item['symbol']
        price = item['price']

        # Обновляем цену
        ticker, _ = Ticker.objects.update_or_create(
            exchange=exchange,
            symbol=symbol,
            defaults={'last_price': price}
        )
        
        # Получаем фандинг
        # ВАЖНО: В фоновой задаче лучше не грузить историю за 30 дней каждый раз.
        # Если база пустая - грузим всё. Если есть данные - можно грузить меньше.
        # Но пока оставим 30 дней для надежности.
        history = scanner.get_funding_history(ticker.symbol, days=30)
        
        new_records = []
        for row in history:
            # Проверка на существование (чтобы не дублировать)
            # Оптимизация: проверяем наличие только если дата свежая, но для надежности exists() ок
            if not FundingRate.objects.filter(ticker=ticker, timestamp=row['timestamp']).exists():
                
                # Расчет APR
                periods_per_day = 24 / row['period_hours']
                apr_val = row['rate'] * Decimal(periods_per_day) * 365 * 100
                
                new_records.append(FundingRate(
                    ticker=ticker,
                    timestamp=row['timestamp'],
                    rate=row['rate'],
                    period_hours=row['period_hours'],
                    apr=apr_val
                ))
        
        if new_records:
            FundingRate.objects.bulk_create(new_records)
            processed_count += len(new_records)

    return f"Готово. Добавлено записей: {processed_count}"

@shared_task
def scan_bitget_task():
    print("Старт фоновой задачи: Bitget")
    exchange, _ = Exchange.objects.get_or_create(name="Bitget")
    scanner = BitgetScanner()
    
    market_data = scanner.get_tickers()
    processed = 0

    # Берем только топ-20 монет для теста, чтобы не упереться в лимиты сразу
    for item in market_data[:20]: 
        ticker, _ = Ticker.objects.update_or_create(
            exchange=exchange,
            symbol=item['symbol'],
            defaults={'last_price': item['price']}
        )
        
        history = scanner.get_funding_history(ticker.symbol)
        for row in history:
            if not FundingRate.objects.filter(ticker=ticker, timestamp=row['timestamp']).exists():
                # Расчет APR (365 дней * 3 периода по 8 часов)
                apr_val = row['rate'] * 3 * 365 * 100
                FundingRate.objects.create(
                    ticker=ticker,
                    timestamp=row['timestamp'],
                    rate=row['rate'],
                    period_hours=8,
                    apr=apr_val
                )
                processed += 1
    return f"Bitget готов. Добавлено: {processed}"