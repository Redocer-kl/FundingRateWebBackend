from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .models import Favorite, Asset, Ticker, Asset, Exchange, FundingRate, ArbitragePosition, HyperliquidAgent, UserExchangeCredential, ParadexAgent
from starknet_py.net.signer.stark_curve_signer import KeyPair
from .serializers import UserSerializer, FavoriteSerializer, AssetSerializer, ExchangeSerializer, ArbitragePositionSerializer, UserExchangeCredentialSerializer, ParadexAgentSerializer
from django.db.models import Avg, Prefetch
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import requests
from rest_framework.permissions import AllowAny
import time
from functools import lru_cache
from eth_account import Account
from .utils.encryption import EncryptionUtil
from hyperliquid.exchange import Exchange as ExchangeHL
from hyperliquid.utils import constants
from eth_account import Account as EthAccount

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
        fav_serializer = FavoriteSerializer(favorites, many=True)
        

        positions = ArbitragePosition.objects.filter(user=user)
        pos_serializer = ArbitragePositionSerializer(positions, many=True)
        
        return Response({
            "username": user.username,
            "email": user.email,
            "favorites": fav_serializer.data,
            "positions": pos_serializer.data  
        })
    
class ClosePositionView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        try:
            position = ArbitragePosition.objects.get(pk=pk, user=request.user)
            
            position.status = 'CLOSED'
            position.save()
            
            return Response({"message": "Позиция закрыта успешно"}, status=200)
        except ArbitragePosition.DoesNotExist:
            return Response({"error": "Позиция не найдена"}, status=404)
        
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
        
class ArbitragePositionView(APIView):
    permission_classes = [permissions.IsAuthenticated] 

    def get(self, request):
        positions = ArbitragePosition.objects.filter(user=request.user).order_by('-created_at')
        serializer = ArbitragePositionSerializer(positions, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Создать новую арбитражную позицию"""
        serializer = ArbitragePositionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class GenerateAgentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Возвращает текущего агента пользователя, если он есть"""
        agent = HyperliquidAgent.objects.filter(user=request.user).last()
        if not agent:
            return Response({"agent": None})
        
        return Response({
            "agent_address": agent.agent_address,
            "is_approved": agent.is_approved,
            "created_at": agent.created_at
        })

    def post(self, request):
        """Генерирует нового агента"""
        account = Account.create()
        agent_address = account.address
        private_key = account.key.hex()

        HyperliquidAgent.objects.filter(user=request.user).delete()
        
        agent = HyperliquidAgent.objects.create(
            user=request.user,
            agent_address=agent_address
        )
        agent.set_private_key(private_key)
        agent.save()

        return Response({
            "agent_address": agent_address,
            "is_approved": False,
            "message": "Agent generated. Please approve on frontend."
        })
    
class ApproveAgentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        agent = HyperliquidAgent.objects.filter(user=request.user).last()
        if not agent:
            return Response({"error": "No agent found"}, status=404)

        signature = request.data.get('signature')
        payload = request.data.get('payload')

        if not signature or not payload:
            return Response({"error": "Signature and payload required"}, status=400)

        try:
            agent_account = EthAccount.from_key(agent.get_private_key())  
            agent.is_approved = True
            agent.save()
            
            return Response({"status": "success", "message": "Agent activated on backend"})
        except Exception as e:
            return Response({"error": str(e)}, status=500)
    
class UserExchangeCredentialView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Список всех подключенных бирж пользователя"""
        credentials = UserExchangeCredential.objects.filter(user=request.user)
        serializer = UserExchangeCredentialSerializer(credentials, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Добавление или обновление ключей"""
        serializer = UserExchangeCredentialSerializer(data=request.data)
        
        if serializer.is_valid():
            exchange_obj = serializer.validated_data['exchange'] 
            api_key = serializer.validated_data['api_key']
            api_secret = serializer.validated_data['api_secret']
            passphrase = serializer.validated_data.get('passphrase')
            private_key = serializer.validated_data.get('private_key')

            credential, created = UserExchangeCredential.objects.get_or_create(
                user=request.user,
                exchange=exchange_obj
            )

            credential.set_keys(
                api_key=api_key,
                api_secret=api_secret,
                passphrase=passphrase,
                private_key=private_key
            )
            
            credential.is_valid = True
            credential.error_message = None
            credential.save()

            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response(
                UserExchangeCredentialSerializer(credential).data, 
                status=status_code
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Удаление ключей по ID"""
        cred_id = request.data.get('id') or request.query_params.get('id')
        
        if not cred_id:
            return Response({"error": "ID required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            credential = UserExchangeCredential.objects.get(id=cred_id, user=request.user)
            credential.delete()
            return Response({"message": "Credential deleted"}, status=status.HTTP_200_OK)
        except UserExchangeCredential.DoesNotExist:
            return Response({"error": "Credential not found"}, status=status.HTTP_404_NOT_FOUND)
        
class ParadexAgentGenerateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Получить текущего агента Paradex"""
        agent = ParadexAgent.objects.filter(user=request.user).last()
        if not agent:
            return Response({"agent": None})
        serializer = ParadexAgentSerializer(agent)
        return Response(serializer.data)

    def post(self, request):
        """Генерация нового Starknet-агента"""
        key_pair = KeyPair.generate()
        private_key_hex = hex(key_pair.private_key)
        public_key_hex = hex(key_pair.public_key)

        ParadexAgent.objects.filter(user=request.user).delete()
        
        agent = ParadexAgent.objects.create(
            user=request.user,
            stark_public_key=public_key_hex
        )
        agent.set_private_key(private_key_hex)
        agent.save()

        return Response({
            "stark_public_key": public_key_hex,
            "is_approved": False,
            "message": "Paradex agent generated. Please sign message in MetaMask."
        }, status=status.HTTP_201_CREATED)

class ParadexAgentApproveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Принимает подпись от фронтенда и активирует агента"""
        signature = request.data.get('signature')
        
        agent = ParadexAgent.objects.filter(user=request.user).last()
        if not agent:
            return Response({"error": "No agent found"}, status=status.HTTP_404_NOT_FOUND)

        if not signature:
            return Response({"error": "Signature required"}, status=status.HTTP_400_BAD_REQUEST)

        agent.is_approved = True
        agent.save()

        return Response({"status": "success", "message": "Paradex agent approved"})