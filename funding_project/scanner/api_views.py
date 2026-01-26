from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .models import Favorite, Asset, Ticker, Asset, Exchange, FundingRate
from .serializers import UserSerializer, FavoriteSerializer, AssetSerializer, ExchangeSerializer
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Prefetch

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer

class ProfileView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        favorites = Favorite.objects.filter(user=user)
        serializer = FavoriteSerializer(favorites, many=True)
        return Response({
            "username": user.username,
            "email": user.email,
            "favorites": serializer.data
        })

class ToggleFavoriteView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        symbol = request.data.get('asset_symbol')
        
        try:
            asset_obj = Asset.objects.get(symbol=symbol)
        except Asset.DoesNotExist:
            return Response({"error": f"Asset {symbol} not found"}, status=404)

        fav, created = Favorite.objects.get_or_create(
            user=request.user,
            asset=asset_obj,
            exchange=None 
        )
        
        if not created:
            fav.delete()
            return Response({"status": "removed"})
        
        return Response({"status": "added"})

class FundingTableAPIView(APIView):
    def get(self, request):
        period = request.query_params.get('period', '1d')
        search = request.query_params.get('q', '').upper()
        sort_by = request.query_params.get('sort', 'spread')
        exchanges = request.query_params.getlist('exchanges')
        
        page_number = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 10)

        days_map = {'1h': 0.04, '4h': 0.16, '1d': 1, '3d': 3, '7d': 7, '30d': 30}
        time_threshold = timezone.now() - timedelta(days=days_map.get(period, 1))

        rates_queryset = FundingRate.objects.filter(
            timestamp__gte=time_threshold
        ).order_by('timestamp') 

        tickers = Ticker.objects.select_related('exchange', 'asset').prefetch_related(
            Prefetch('funding_rates', queryset=rates_queryset, to_attr='cached_rates')
        )
        
        if search:
            tickers = tickers.filter(symbol__icontains=search)
        if exchanges:
            tickers = tickers.filter(exchange__name__in=exchanges)

        grouped_data = {}
        for t in tickers:
            rates = t.cached_rates
            if not rates:
                continue

            latest = rates[-1]
            
            total_apr = sum(r.apr for r in rates)
            avg_apr = total_apr / len(rates)

            frequency = 0
            if len(rates) >= 2:
                diff = rates[-1].timestamp - rates[-2].timestamp
                hours = diff.total_seconds() / 3600
                if hours > 0:
                    frequency = round(24 / hours)

            history_values = [float(r.apr) for r in rates]

            row = {
                'exchange': t.exchange.name,
                'price': t.last_price,
                'live_apr': float(latest.apr),     
                'hist_apr': float(avg_apr),       
                'frequency': frequency,          
                'history': history_values,       
                'image': t.asset.image_url if t.asset else None,
                'market_cap': t.asset.market_cap if t.asset else 0,
                'volume': t.asset.volume_24h if t.asset else 0,
            }

            symbol = t.symbol
            if symbol not in grouped_data:
                grouped_data[symbol] = []
            grouped_data[symbol].append(row)

        result = []
        for symbol, rows in grouped_data.items():
            aprs = [r['hist_apr'] for r in rows]
            spread = max(aprs) - min(aprs) if len(aprs) > 1 else 0
            
            result.append({
                'symbol': symbol,
                'asset_info': rows[0], 
                'spread': spread,
                'exchanges_data': rows
            })

        if sort_by == 'market_cap':
            result.sort(key=lambda x: x['asset_info']['market_cap'] or 0, reverse=True)
        elif sort_by == 'apr':
            result.sort(key=lambda x: max([abs(r['live_apr']) for r in x['exchanges_data']]), reverse=True)
        else:
            result.sort(key=lambda x: x['spread'], reverse=True)

        paginator = Paginator(result, page_size)
        try:
            page_obj = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            page_obj = paginator.page(1)

        return Response({
            'count': paginator.count,     
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'results': list(page_obj)       
        })

class CoinDetailAPIView(APIView):
    def get(self, request, symbol):
        time_threshold = timezone.now() - timedelta(days=30)
        
        tickers = Ticker.objects.filter(symbol=symbol).select_related('exchange', 'asset')
        
        if not tickers.exists():
            return Response({"error": "Symbol not found"}, status=404)

        asset_data = AssetSerializer(tickers.first().asset).data if tickers.first().asset else None
        
        history = []
        summary_stats = []

        for t in tickers:
            rates_qs = t.funding_rates.filter(timestamp__gte=time_threshold).order_by('timestamp')
            
            points = list(rates_qs.values('timestamp', 'apr'))
            history.append({
                'exchange': t.exchange.name,
                'points': [{'t': p['timestamp'], 'v': p['apr']} for p in points]
            })

            avg_apr = rates_qs.aggregate(Avg('apr'))['apr__avg'] or 0
            
            latest_rate = rates_qs.last()
            
            summary_stats.append({
                'exchange': t.exchange.name,
                'current_apr': latest_rate.apr if latest_rate else 0,
                'avg_apr': round(avg_apr, 2),
                'price': float(t.last_price) if t.last_price else 0
            })

        return Response({
            'symbol': symbol,
            'asset': asset_data,
            'summary_stats': summary_stats,
            'history': history
        })
    
class ScannerStatsView(APIView):
    def get(self, request):
        stats = {
            'total_coins': Ticker.objects.values('symbol').distinct().count(),
            'total_exchanges': Exchange.objects.count(),
            'last_update': FundingRate.objects.order_by('-timestamp').first().timestamp if FundingRate.objects.exists() else None
        }
        return Response(stats)
    


class BestOpportunitiesAPIView(APIView):
    def get(self, request):
        period_param = request.query_params.get('period', '1d')
        search_query = request.query_params.get('q', '').strip().upper()
        side_filter = request.query_params.get('side', 'ALL')
        
        page_number = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 30)

        days_map = {'1d': 1, '3d': 3, '7d': 7, '14d': 14, '30d': 30}
        time_threshold = timezone.now() - timedelta(days=days_map.get(period_param, 1))

        tickers = Ticker.objects.select_related('exchange').prefetch_related(
            Prefetch('funding_rates', 
                     queryset=FundingRate.objects.filter(timestamp__gte=time_threshold),
                     to_attr='filtered_rates')
        )

        if search_query:
            tickers = tickers.filter(symbol__icontains=search_query)

        opportunities = []
        for t in tickers:
            rates = t.filtered_rates 
            if not rates: continue

            avg_apr = sum(r.apr for r in rates) / len(rates)
            if avg_apr == 0: continue

            current_side = 'SHORT' if avg_apr > 0 else 'LONG'
            yield_val = abs(float(avg_apr))

            if side_filter != 'ALL' and side_filter != current_side:
                continue

            opportunities.append({
                'symbol': t.symbol,
                'exchange': t.exchange.name,
                'apr': round(yield_val, 2),
                'side': current_side,
                'price': float(t.last_price) if t.last_price else 0,
            })

        opportunities.sort(key=lambda x: x['apr'], reverse=True)

        paginator = Paginator(opportunities, page_size)
        try:
            page_obj = paginator.page(page_number)
        except:
            page_obj = paginator.page(1)

        return Response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'results': list(page_obj)
        })