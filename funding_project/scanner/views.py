from django.shortcuts import render
from django.db.models import Avg, Max, Min
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from .models import Ticker, FundingRate

def funding_table(request):
    period_param = request.GET.get('period', '1d')
    page_number = request.GET.get('page', 1)
    search_query = request.GET.get('q', '').strip().upper()
    
    # Фильтры по APR (например, показывать только где APR > 20%)
    min_apr_filter = request.GET.get('min_apr')
    
    days_map = {'1d': 1, '3d': 3, '7d': 7, '14d': 14, '30d': 30}
    days = days_map.get(period_param, 1)
    time_threshold = timezone.now() - timedelta(days=days)

    tickers = Ticker.objects.all().select_related('exchange').prefetch_related('funding_rates')
    
    if search_query:
        tickers = tickers.filter(symbol__icontains=search_query)

    grouped_data = {}
    symbol_spreads = {} # Для хранения разницы между биржами

    for ticker in tickers:
        symbol = ticker.symbol
        latest_funding = ticker.funding_rates.order_by('-timestamp').first()
        if not latest_funding: continue

        history_stats = ticker.funding_rates.filter(
            timestamp__gte=time_threshold
        ).aggregate(
            avg_apr=Avg('apr'), 
            avg_rate=Avg('rate')
        )
        
        avg_apr = history_stats['avg_apr'] or 0
        
        # Определяем рекомендацию: если APR положительный — мы получаем деньги в Шорте
        # Если отрицательный — мы получаем деньги в Лонге
        side = "SHORT" if avg_apr >= 0 else "LONG"

        row_data = {
            'ticker_id': ticker.id,
            'exchange': ticker.exchange.name,
            'price': ticker.last_price,
            'live_rate': latest_funding.rate * 100,
            'live_apr': latest_funding.apr,
            'hist_apr': avg_apr,
            'hist_rate': (history_stats['avg_rate'] or 0) * 100,
            'payouts': int(24 / latest_funding.period_hours) if latest_funding.period_hours else 3,
            'side': side
        }

        if symbol not in grouped_data:
            grouped_data[symbol] = []
        
        grouped_data[symbol].append(row_data)

    # Вычисляем спред для каждого символа
    final_grouped_data = {}
    for symbol, rows in grouped_data.items():
        if len(rows) > 1:
            aprs = [r['hist_apr'] for r in rows]
            spread = max(aprs) - min(aprs)
        else:
            spread = 0
        
        symbol_spreads[symbol] = spread
        final_grouped_data[symbol] = rows

    # Сортировка по размеру спреда (самые выгодные связки сверху)
    sorted_symbols_list = sorted(
        final_grouped_data.keys(), 
        key=lambda s: symbol_spreads[s], 
        reverse=True
    )
    
    paginator = Paginator(sorted_symbols_list, 20)
    page_obj = paginator.get_page(page_number)

    context = {
        'grouped_data': final_grouped_data,
        'symbol_spreads': symbol_spreads,
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
    summary_stats = []
    colors = {'Hyperliquid': '#f0b90b', 'Bitget': '#00f0ff', 'Paradex': '#ff4747'}

    for ticker in tickers:
        exch_name = ticker.exchange.name
        rates = ticker.funding_rates.filter(timestamp__gte=time_threshold).order_by('timestamp')
        
        # Данные для графика
        data_points = [{'x': r.timestamp.isoformat(), 'y': float(r.apr)} for r in rates]
        
        # Сводная статистика для карточек
        avg_data = rates.aggregate(avg_apr=Avg('apr'), max_apr=Max('apr'))
        latest = rates.last()
        
        if latest:
            summary_stats.append({
                'exchange': exch_name,
                'avg_apr': avg_data['avg_apr'] or 0,
                'current_apr': latest.apr,
                'price': ticker.last_price,
                'color': colors.get(exch_name, '#ffffff')
            })

        datasets.append({
            'label': exch_name,
            'data': data_points,
            'borderColor': colors.get(exch_name, '#ffffff'),
            'backgroundColor': colors.get(exch_name, '#ffffff'),
            'borderWidth': 2,
            'fill': False,
            'tension': 0.1,
            'pointRadius': 2,
            'spanGaps': True
        })

    chart_data = {'datasets': datasets}

    return render(request, 'scanner/coin_detail.html', {
        'symbol': symbol,
        'chart_data': chart_data,
        'summary_stats': summary_stats
    })