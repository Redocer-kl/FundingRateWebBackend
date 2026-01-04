from celery import shared_task
from .models import Exchange, Ticker, FundingRate
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal, getcontext
import time

getcontext().prec = 28

from .exchanges.bitget import BitgetScanner
from .exchanges.hyperliquid import HyperliquidScanner
from .exchanges.paradex import ParadexScanner

SCANNERS = {
    'Bitget': BitgetScanner,
    'Hyperliquid': HyperliquidScanner,
    'Paradex': ParadexScanner,
}

@shared_task
def scan_exchange_task(exchange_name):
    if exchange_name not in SCANNERS:
        return f"Сканер для {exchange_name} не найден"
    
    scanner = SCANNERS[exchange_name]()
    market_data = scanner.fetch_tickers()
    if not market_data:
        return f"{exchange_name}: Нет данных тикеров"
    
    exchange_obj, _ = Exchange.objects.get_or_create(name=exchange_name)
    processed_count = 0
    
    for item in market_data:
        ticker, _ = Ticker.objects.update_or_create(
            exchange=exchange_obj,
            symbol=item['symbol'],
            defaults={'last_price': item['price']}
        )
        
        last_entry = FundingRate.objects.filter(ticker=ticker).order_by('-timestamp').first()
        lookback = 1 if last_entry else 30
        
        history = scanner.fetch_funding_history(item.get('original_symbol', item['symbol']), lookback_days=lookback)
        
        existing_ts = set(FundingRate.objects.filter(
            ticker=ticker, 
            timestamp__gte=timezone.now() - timedelta(days=lookback + 1)
        ).values_list('timestamp', flat=True))

        new_records = []
        for row in history:
            if row['timestamp'] in existing_ts:
                continue
                
            rate = Decimal(str(row['rate']))
            period = Decimal(str(row.get('period_hours', 1)))
            
            # Стандартная формула APR
            apr_val = rate * (Decimal('24') / period) * Decimal('365') * Decimal('100')
            
            # Технический фильтр от мусора
            if abs(apr_val) > Decimal('2000'):
                continue

            new_records.append(FundingRate(
                ticker=ticker,
                timestamp=row['timestamp'],
                rate=rate,
                period_hours=float(period),
                apr=apr_val.quantize(Decimal("0.0001"))
            ))
            existing_ts.add(row['timestamp'])
        
        if new_records:
            FundingRate.objects.bulk_create(new_records, ignore_conflicts=True)
            processed_count += len(new_records)
        
        time.sleep(0.05) # Небольшая пауза
            
    return f"{exchange_name}: Успешно обновлено {processed_count} записей"