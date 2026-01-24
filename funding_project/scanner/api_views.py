from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .models import Favorite, Asset, Ticker, Asset, Exchange
from .serializers import UserSerializer, FavoriteSerializer, AssetSerializer, ExchangeSerializer
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta

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
        asset_id = request.data.get('asset_id')
        exchange_id = request.data.get('exchange_id')
        
        fav, created = Favorite.objects.get_or_create(
            user=request.user,
            asset_id=asset_id,
            exchange_id=exchange_id
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

        days_map = {'1d': 1, '3d': 3, '7d': 7, '14d': 14, '30d': 30}
        time_threshold = timezone.now() - timedelta(days=days_map.get(period, 1))

        tickers = Ticker.objects.select_related('exchange', 'asset').prefetch_related('funding_rates')
        if search:
            tickers = tickers.filter(symbol__icontains=search)
        if exchanges:
            tickers = tickers.filter(exchange_id__in=exchanges)

        grouped_data = {}
        for t in tickers:
            symbol = t.symbol
            latest = t.funding_rates.order_by('-timestamp').first()
            if not latest: continue

            stats = t.funding_rates.filter(timestamp__gte=time_threshold).aggregate(avg_apr=Avg('apr'))
            
            row = {
                'exchange': t.exchange.name,
                'price': t.last_price,
                'live_apr': latest.apr,
                'hist_apr': stats['avg_apr'] or 0,
                'image': t.asset.image_url if t.asset else None,
                'market_cap': t.asset.market_cap if t.asset else 0,
                'volume': t.asset.volume_24h if t.asset else 0,
            }

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
            result.sort(key=lambda x: x['asset_info']['market_cap'], reverse=True)
        elif sort_by == 'apr':
            result.sort(key=lambda x: max([abs(r['hist_apr']) for r in x['exchanges_data']]), reverse=True)
        else:
            result.sort(key=lambda x: x['spread'], reverse=True)

        return Response(result)

class CoinDetailAPIView(APIView):
    def get(self, request, symbol):
        time_threshold = timezone.now() - timedelta(days=30)
        tickers = Ticker.objects.filter(symbol=symbol).select_related('exchange', 'asset')
        
        asset_data = None
        if tickers.exists() and tickers.first().asset:
            asset_data = AssetSerializer(tickers.first().asset).data

        history = []
        for t in tickers:
            rates = t.funding_rates.filter(timestamp__gte=time_threshold).order_by('timestamp')
            history.append({
                'exchange': t.exchange.name,
                'points': [{'t': r.timestamp, 'v': r.apr} for r in rates]
            })

        return Response({
            'symbol': symbol,
            'asset': asset_data,
            'history': history
        })