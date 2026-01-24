from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Max
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from .models import Ticker, Exchange, Asset, FundingRate

def funding_table(request):
    period_param = request.GET.get('period', '1d')
    page_number = request.GET.get('page', 1)
    search_query = request.GET.get('q', '').strip().upper()
    sort_by = request.GET.get('sort', 'spread')  
    selected_exchanges = request.GET.getlist('exchanges') 

    days_map = {'1d': 1, '3d': 3, '7d': 7, '14d': 14, '30d': 30}
    days = days_map.get(period_param, 1)
    time_threshold = timezone.now() - timedelta(days=days)
    
    all_exchanges = Exchange.objects.all()

    tickers = Ticker.objects.all().select_related('exchange', 'asset').prefetch_related('funding_rates')
    
    if search_query:
        tickers = tickers.filter(symbol__icontains=search_query)
    
    if selected_exchanges:
        tickers = tickers.filter(exchange_id__in=selected_exchanges)

    grouped_data = {}
    symbol_spreads = {}
    symbol_assets = {} 
    symbol_max_apr = {} 

    for ticker in tickers:
        symbol = ticker.symbol
        
        if symbol not in symbol_assets and ticker.asset:
            symbol_assets[symbol] = {
                'image': ticker.asset.image_url,
                'market_cap': ticker.asset.market_cap or 0,
                'volume': ticker.asset.volume_24h or 0,
                'asset_symbol': ticker.asset.symbol 
            }

        latest_funding = ticker.funding_rates.order_by('-timestamp').first()
        if not latest_funding: continue

        history_stats = ticker.funding_rates.filter(
            timestamp__gte=time_threshold
        ).aggregate(avg_apr=Avg('apr'), avg_rate=Avg('rate'))
         
        avg_apr = history_stats['avg_apr'] or 0
        
        row_data = {
            'exchange': ticker.exchange.name,
            'price': ticker.last_price,
            'live_rate': latest_funding.rate * 100,
            'live_apr': latest_funding.apr,
            'hist_apr': avg_apr,
            'hist_rate': (history_stats['avg_rate'] or 0) * 100,
            'payouts': int(24 / latest_funding.period_hours) if latest_funding.period_hours else 3,
            'side': "SHORT" if avg_apr >= 0 else "LONG"
        }

        if symbol not in grouped_data:
            grouped_data[symbol] = []
        grouped_data[symbol].append(row_data)

    final_symbols = []
    for symbol, rows in grouped_data.items():
        if len(rows) > 1:
            aprs = [r['hist_apr'] for r in rows]
            spread = max(aprs) - min(aprs)
            max_abs_apr = max([abs(r['hist_apr']) for r in rows])
        else:
            spread = 0
            max_abs_apr = abs(rows[0]['hist_apr']) if rows else 0
        
        symbol_spreads[symbol] = spread
        symbol_max_apr[symbol] = max_abs_apr
        final_symbols.append(symbol)

    if sort_by == 'symbol':
        final_symbols.sort()
    elif sort_by == 'market_cap':
        final_symbols.sort(key=lambda s: symbol_assets.get(s, {}).get('market_cap', 0), reverse=True)
    elif sort_by == 'volume':
        final_symbols.sort(key=lambda s: symbol_assets.get(s, {}).get('volume', 0), reverse=True)
    elif sort_by == 'apr':
        final_symbols.sort(key=lambda s: symbol_max_apr.get(s, 0), reverse=True)
    else:
        final_symbols.sort(key=lambda s: symbol_spreads.get(s, 0), reverse=True)

    paginator = Paginator(final_symbols, 20)
    page_obj = paginator.get_page(page_number)

    return render(request, 'scanner/table.html', {
        'grouped_data': grouped_data,
        'symbol_spreads': symbol_spreads,
        'symbol_assets': symbol_assets, 
        'page_obj': page_obj,
        'current_period': period_param,
        'search_query': search_query,
        'all_exchanges': all_exchanges,
        'selected_exchanges': [int(x) for x in selected_exchanges],
        'current_sort': sort_by
    })

def coin_detail(request, symbol):
    tickers = Ticker.objects.filter(symbol=symbol).select_related('exchange', 'asset')
    time_threshold = timezone.now() - timedelta(days=30)
    
    asset_info = None
    if tickers.exists() and tickers.first().asset:
        asset_info = tickers.first().asset

    datasets = []
    summary_stats = []
    colors = {'Hyperliquid': '#f0b90b', 'Bitget': '#00f0ff', 'Paradex': '#ff4747', 'Binance': "#f1e21a", 'Kucoin': "#ef14ff"}

    for ticker in tickers:
        exch_name = ticker.exchange.name
        rates = ticker.funding_rates.filter(timestamp__gte=time_threshold).order_by('timestamp')
        
        data_points = [{'x': r.timestamp.isoformat(), 'y': float(r.apr)} for r in rates]
        
        avg_data = rates.aggregate(avg_apr=Avg('apr'))
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
        'asset': asset_info, 
        'chart_data': chart_data,
        'summary_stats': summary_stats
    })

def best_opportunities(request):
    period_param = request.GET.get('period', '1d')
    search_query = request.GET.get('q', '').strip().upper()
    side_filter = request.GET.get('side', 'ALL') 
    selected_exchanges = request.GET.getlist('exchanges')

    days_map = {'1d': 1, '3d': 3, '7d': 7, '14d': 14, '30d': 30}
    days = days_map.get(period_param, 1)
    time_threshold = timezone.now() - timedelta(days=days)
    
    all_exchanges = Exchange.objects.all()
    tickers = Ticker.objects.all().select_related('exchange').prefetch_related('funding_rates')

    # Фильтры
    if search_query:
        tickers = tickers.filter(symbol__icontains=search_query)
    if selected_exchanges:
        tickers = tickers.filter(exchange_id__in=selected_exchanges)

    opportunities = []

    for ticker in tickers:
        stats = ticker.funding_rates.filter(
            timestamp__gte=time_threshold
        ).aggregate(avg_apr=Avg('apr'))
        
        avg_apr = stats['avg_apr'] or 0
        if avg_apr == 0: continue

        if avg_apr > 0:
            current_side = 'SHORT'
            yield_val = avg_apr
        else:
            current_side = 'LONG'
            yield_val = abs(avg_apr)

        if side_filter != 'ALL' and side_filter != current_side:
            continue

        opportunities.append({
            'symbol': ticker.symbol,
            'exchange': ticker.exchange.name,
            'apr': yield_val,
            'side': current_side,
            'price': ticker.last_price,
            'color': '#02c076' if current_side == 'LONG' else '#f84960'
        })

    opportunities.sort(key=lambda x: x['apr'], reverse=True)

    paginator = Paginator(opportunities, 30)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'scanner/best_opportunities.html', {
        'page_obj': page_obj,
        'all_exchanges': all_exchanges,
        'current_period': period_param,
        'current_side': side_filter,
        'selected_exchanges': [int(x) for x in selected_exchanges],
        'search_query': search_query
    })

def index(request):
    stats = {
        'total_coins': Ticker.objects.values('symbol').distinct().count(),
        'total_exchanges': Exchange.objects.count(),
        'last_update': FundingRate.objects.order_by('-timestamp').first()
    }
    return render(request, 'scanner/index.html', {'stats': stats})