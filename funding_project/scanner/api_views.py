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
import requests
from rest_framework.permissions import AllowAny
import time
from functools import lru_cache

class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
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
    permission_classes = [AllowAny]
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
    permission_classes = [AllowAny]
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
    permission_classes = [AllowAny]
    def get(self, request):
        stats = {
            'total_coins': Ticker.objects.values('symbol').distinct().count(),
            'total_exchanges': Exchange.objects.count(),
            'last_update': FundingRate.objects.order_by('-timestamp').first().timestamp if FundingRate.objects.exists() else None
        }
        return Response(stats)
    


class BestOpportunitiesAPIView(APIView):
    permission_classes = [AllowAny]
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
    
class ExchangeProxyView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        paradex_session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json"
        }
        exchange = request.query_params.get('exchange', '').lower()
        symbol = request.query_params.get('symbol', '').upper().strip().replace(" ", "")
        interval = request.query_params.get('interval', '1m')
        limit = request.query_params.get('limit', '150')

        if not exchange or not symbol:
            return Response({"error": "Exchange and symbol required"}, status=400)

        try:
            # --- BINANCE ---
            if exchange == 'binance':
                url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
                res = requests.get(url, timeout=10)

            # --- COINEX ---
            elif exchange == 'coinex':
                coinex_interval = '1min' if interval == '1m' else interval
                url = f"https://api.coinex.com/perpetual/v1/market/kline?market={symbol}&type={coinex_interval}&limit={limit}"
                res = requests.get(url, timeout=10)

            # --- KUCOIN ---
            elif exchange == 'kucoin':
                k_symbol = symbol if symbol.endswith('M') else f"{symbol}M"
                granularity = 1 
                url = f"https://api-futures.kucoin.com/api/v1/kline/query?symbol={k_symbol}&granularity={granularity}"
                res = requests.get(url, headers=headers, timeout=10)

            # --- BITGET ---
            elif exchange == 'bitget':
                url = f"https://api.bitget.com/api/v2/mix/market/candles?symbol={symbol}&granularity=1m&limit={limit}&productType=usdt-margined"
                res = requests.get(url, timeout=10)

            # --- PARADEX ---
            elif exchange == 'paradex':

                @lru_cache(maxsize=2000)
                def get_pyth_feed_id(symbol_name):
                    try:
                        clean_symbol = symbol_name.replace('USDT', '').replace('USD', '')
                        search_url = f"https://benchmarks.pyth.network/v1/price_feeds?query={clean_symbol}&asset_type=crypto"
                        search_res = requests.get(search_url, timeout=5)
                        if search_res.status_code == 200:
                            feeds = search_res.json()
                            for feed in feeds:
                                if clean_symbol in feed['attributes']['symbol']:
                                    return feed['id']
                        return None
                    except Exception as e:
                        print(f"Pyth Search Error: {e}")
                        return None

                feed_id = get_pyth_feed_id(symbol)
                
                if not feed_id:
                    feed_id = "ff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace"

                end_time = int(time.time())
                start_time = end_time - (int(limit) * 60)
                
                url = "https://benchmarks.pyth.network/v1/shims/tradingview/history"
                
                params = {
                    "symbol": f"Crypto.{symbol.replace('USDT', '')}/USD",
                    "resolution": "1",
                    "from": start_time,
                    "to": end_time
                }
                
                res = requests.get(url, params=params, timeout=10)
                
                if res.status_code == 200:
                    return Response(res.json())
                else:
                    return Response({"error": "Pyth history failed"}, status=502)

            # --- HYPERLIQUID ---
            elif exchange == 'hyperliquid':
                url = "https://api.hyperliquid.xyz/info"
                h_symbol = symbol.replace('USDT', '')
                payload = {
                    "type": "candleSnapshot",
                    "req": {"coin": h_symbol, "interval": "1m", "startTime": 0}
                }
                res = requests.post(url, json=payload, headers=headers, timeout=10)
            
            else:
                return Response({"error": "Not supported"}, status=400)

            res.raise_for_status()
            return Response(res.json(), status=res.status_code)

        except Exception as e:
            print(f"Proxy Error [{exchange}]: {e}")
            return Response({"error": str(e)}, status=502)

class KucoinTokenView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        try:
            url = "https://api-futures.kucoin.com/api/v1/bullet-public"
            res = requests.post(url, timeout=5)
            return Response(res.json())
        except Exception as e:
            return Response({"error": str(e)}, status=500)