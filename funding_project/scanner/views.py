from django.shortcuts import render
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator # Добавляем пагинатор
from .models import Ticker, FundingRate

def funding_table(request):
    period_param = request.GET.get('period', '1d')
    page_number = request.GET.get('page', 1)
    search_query = request.GET.get('q', '').strip().upper() # Поиск
    
    days_map = {'1d': 1, '3d': 3, '7d': 7, '14d': 14, '30d': 30}
    days = days_map.get(period_param, 1)
    time_threshold = timezone.now() - timedelta(days=days)

    # Фильтруем тикеры, если есть поисковый запрос
    tickers = Ticker.objects.all().select_related('exchange')
    if search_query:
        tickers = tickers.filter(symbol__icontains=search_query)

    grouped_data = {}
    symbol_max_apr = {}

    for ticker in tickers:
        symbol = ticker.symbol
        latest_funding = ticker.funding_rates.order_by('-timestamp').first()
        if not latest_funding: continue

        history_stats = ticker.funding_rates.filter(timestamp__gte=time_threshold).aggregate(
            avg_apr=Avg('apr'), avg_rate=Avg('rate')
        )
        
        avg_apr = history_stats['avg_apr'] or 0
        
        row_data = {
            'ticker_id': ticker.id, # Для ссылки на страницу монеты
            'exchange': ticker.exchange.name,
            'price': ticker.last_price,
            'live_rate': latest_funding.rate,
            'live_apr': latest_funding.apr,
            'hist_apr': avg_apr,
            'hist_rate': history_stats['avg_rate'] or 0,
            'payouts': int(24 / latest_funding.period_hours)
        }

        if symbol not in grouped_data:
            grouped_data[symbol] = []
            symbol_max_apr[symbol] = -999999
        
        grouped_data[symbol].append(row_data)
        if avg_apr > symbol_max_apr[symbol]:
            symbol_max_apr[symbol] = avg_apr

    sorted_symbols_list = sorted(symbol_max_apr.keys(), key=lambda s: symbol_max_apr[s], reverse=True)
    
    paginator = Paginator(sorted_symbols_list, 20)
    page_obj = paginator.get_page(page_number)

    context = {
        'grouped_data': grouped_data,
        'page_obj': page_obj,
        'current_period': period_param,
        'search_query': search_query,
    }
    return render(request, 'scanner/table.html', context)

import json

def coin_detail(request, symbol):
    tickers = Ticker.objects.filter(symbol=symbol).select_related('exchange')
    time_threshold = timezone.now() - timedelta(days=30)
    
    datasets = []
    colors = {
        'Hyperliquid': '#f0b90b',
        'Bitget': '#00f0ff',
        'Apex': '#ff4747'
    }

    for ticker in tickers:
        exch_name = ticker.exchange.name
        
        # Получаем данные конкретно для этой биржи
        rates = ticker.funding_rates.filter(
            timestamp__gte=time_threshold
        ).order_by('timestamp')
        
        # Формируем список словарей {'x': 'время', 'y': значение}
        # Важно: используем формат ISO для надежности парсинга в JS
        data_points = [
            {
                'x': r.timestamp.isoformat(), 
                'y': float(r.apr)
            } 
            for r in rates
        ]
        
        datasets.append({
            'label': exch_name,
            'data': data_points, # Теперь здесь массив объектов, а не плоский список
            'borderColor': colors.get(exch_name, '#ffffff'),
            'backgroundColor': colors.get(exch_name, '#ffffff'),
            'borderWidth': 2,
            'fill': False,
            'tension': 0.1,
            'pointRadius': 2, # Делаем точки видимыми
            'spanGaps': True
        })

    # 'labels' больше не нужны для типа данных "объект", 
    # Chart.js сам построит шкалу на основе 'x'
    chart_data = {
        'datasets': datasets
    }

    return render(request, 'scanner/coin_detail.html', {
        'symbol': symbol,
        'chart_data': chart_data 
    })