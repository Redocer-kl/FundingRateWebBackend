from django.shortcuts import render
from django.db.models import Avg, Max
from django.utils import timezone
from datetime import timedelta
from .models import Ticker, FundingRate

def funding_table(request):
    # 1. Определяем период из GET-параметра (по умолчанию 1 день)
    period_param = request.GET.get('period', '1d')
    
    # Карта перевода параметра в дни
    days_map = {
        '1d': 1,
        '3d': 3,
        '7d': 7,
        '14d': 14,
        '30d': 30
    }
    days = days_map.get(period_param, 1)
    
    # Вычисляем дату отсечения (сейчас минус N дней)
    time_threshold = timezone.now() - timedelta(days=days)

    # 2. Получаем тикеры Hyperliquid
    # select_related ускоряет запрос, подтягивая данные биржи сразу
    tickers = Ticker.objects.filter(exchange__name='Hyperliquid').select_related('exchange')

    grouped_data = {}

    for ticker in tickers:
        symbol = ticker.symbol
        
        # Получаем последнюю ставку (Live Data)
        latest_funding = ticker.funding_rates.order_by('-timestamp').first()
        
        if not latest_funding:
            continue

        # Считаем среднее за период (Historical Data)
        # aggregate возвращает словарь {'avg_apr': value, 'avg_rate': value}
        history_stats = ticker.funding_rates.filter(timestamp__gte=time_threshold).aggregate(
            avg_apr=Avg('apr'),
            avg_rate=Avg('rate')
        )
        
        avg_apr = history_stats['avg_apr'] or 0
        # "Hist Fund" на скрине часто это средняя ставка за период
        avg_rate = history_stats['avg_rate'] or 0 

        # Формируем объект данных
        row_data = {
            'exchange': ticker.exchange.name,
            'price': ticker.last_price,
            'live_rate': latest_funding.rate,
            'live_apr': latest_funding.apr,
            'hist_apr': avg_apr,
            'hist_rate': avg_rate,
            'payouts': int(24 / latest_funding.period_hours) # Сколько раз в день выплата
        }

        # Группируем по символу
        if symbol not in grouped_data:
            grouped_data[symbol] = []
        grouped_data[symbol].append(row_data)

    # Сортируем монеты по алфавиту (или можно по APR самой первой биржи)
    sorted_symbols = sorted(grouped_data.keys())

    context = {
        'grouped_data': grouped_data,
        'sorted_symbols': sorted_symbols,
        'current_period': period_param
    }
    
    return render(request, 'scanner/table.html', context)