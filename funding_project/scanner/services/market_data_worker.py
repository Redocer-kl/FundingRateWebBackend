import asyncio
import logging
import ujson
import time
import re
import random
import redis.asyncio as redis
import aiohttp
from django.conf import settings
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

class MarketStreamManager:
    def __init__(self):
        self.redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        self.r = None
        self.channel_layer = get_channel_layer()
        self.active_streams = {} 
        self.ref_counts = {}   
        self.session = None

    async def start(self):
        self.r = redis.from_url(self.redis_url, decode_responses=True)
        self.session = aiohttp.ClientSession()
        
        pubsub = self.r.pubsub()
        await pubsub.subscribe('cmd:market_data')
        
        print(f"Market Worker Started. Listening for subscriptions...")

        while True:
            try:
                message = await pubsub.get_message(timeout=0.1)
                if message and message['type'] == 'message':
                    data = ujson.loads(message['data'])
                    await self.handle_command(data)
            except Exception as e:
                logger.error(f"Command error in loop: {e}")
            
            await asyncio.sleep(0.01)

    async def handle_command(self, data):
        action = data.get('action')
        exchange = data.get('exchange')
        symbol = data.get('symbol')
        
        if not exchange or not symbol: 
            return

        key = f"{exchange}:{symbol}".lower()

        if action == 'subscribe':
            self.ref_counts[key] = self.ref_counts.get(key, 0) + 1
            if key not in self.active_streams or self.active_streams[key].done():
                print(f"➕ Subscribing: {exchange} {symbol}")
                self.active_streams[key] = asyncio.create_task(self.stream_router(exchange, symbol))
        
        elif action == 'unsubscribe':
            if key in self.ref_counts:
                self.ref_counts[key] -= 1
                if self.ref_counts[key] <= 0:
                    print(f"➖ Unsubscribing: {exchange} {symbol}")
                    if key in self.active_streams:
                        self.active_streams[key].cancel()
                        del self.active_streams[key]
                    self.ref_counts[key] = 0

    async def stream_router(self, exchange, symbol):
        """Маршрутизатор бирж"""
        ex = exchange.lower()
        try:
            if ex == 'binance': await self.run_binance(symbol)
            elif ex == 'kucoin': await self.run_kucoin(symbol)
            elif ex == 'bitget': await self.run_bitget(symbol)
            elif ex == 'bybit': await self.run_bybit(symbol)
            elif ex == 'coinex': await self.run_coinex(symbol)
            elif ex == 'paradex': await self.run_paradex(symbol)
            elif ex == 'hyperliquid': await self.run_hyperliquid(symbol)
            else:
                logger.warning(f"Unknown exchange: {exchange}")
        except asyncio.CancelledError:
            pass 
        except Exception as e:
            logger.error(f"Stream crashed {exchange} {symbol}: {e}")
            await asyncio.sleep(5) 

    async def broadcast(self, exchange, symbol, bids, asks):
        """Отправка нормализованных данных"""
        payload = {
            "exchange": exchange,
            "symbol": symbol,
            "b": bids[:15] if bids else [],
            "a": asks[:15] if asks else []
        }
        
        await self.r.set(f"book:{exchange.lower()}:{symbol.upper()}", ujson.dumps(payload), ex=5)
        
        group_name = f"market_{exchange.lower()}_{symbol.lower()}"
        await self.channel_layer.group_send(group_name, {
            "type": "market_update",
            "data": payload
        })

    # ==========================================
    #               EXCHANGE LOGIC
    # ==========================================

    async def run_binance(self, symbol):
        url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@depth20@100ms"
        
        async with self.session.ws_connect(url) as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = ujson.loads(msg.data)
                    bids = data.get('bids') or data.get('b')
                    asks = data.get('asks') or data.get('a')
                    await self.broadcast('Binance', symbol, bids, asks)

    async def run_bitget(self, symbol):
        url = "wss://ws.bitget.com/v2/ws/public"
        req = {
            "op": "subscribe",
            "args": [{
                "instType": "USDT-FUTURES",
                "channel": "books15",
                "instId": symbol.upper()
            }]
        }
        async with self.session.ws_connect(url) as ws:
            await ws.send_json(req)
            async for msg in ws:
                if msg.type != aiohttp.WSMsgType.TEXT: continue
                if msg.data == 'pong': continue
                
                data = ujson.loads(msg.data)
                if data.get('action') == 'snapshot' or data.get('action') == 'update':
                    if 'data' in data and len(data['data']) > 0:
                        book = data['data'][0]
                        await self.broadcast('Bitget', symbol, book.get('bids'), book.get('asks'))

    async def run_bybit(self, symbol):
        url = "wss://stream.bybit.com/v5/public/linear"
        req = {"op": "subscribe", "args": [f"orderbook.50.{symbol.upper()}"]}
        
        async with self.session.ws_connect(url) as ws:
            await ws.send_json(req)
            async for msg in ws:
                if msg.type != aiohttp.WSMsgType.TEXT: continue
                data = ujson.loads(msg.data)
                if 'data' in data:
                    d = data['data']
                    await self.broadcast('Bybit', symbol, d.get('b'), d.get('a'))

    async def run_coinex(self, symbol):
        url = "wss://perpetual.coinex.com/"
        req = {
            "method": "depth.subscribe",
            "params": [symbol.upper(), 20, "0", True], 
        }
        req['params'][0] = symbol.upper()
        
        async with self.session.ws_connect(url) as ws:
            await ws.send_json(req)
            async for msg in ws:
                if msg.type != aiohttp.WSMsgType.TEXT: continue
                data = ujson.loads(msg.data)
                
                if data.get('method') == 'depth.update' and data.get('params'):
                    depth = data['params'][1]
                    await self.broadcast('CoinEx', symbol, depth.get('bids'), depth.get('asks'))

    async def run_hyperliquid(self, symbol):
        url = "wss://api.hyperliquid.xyz/ws"
        coin = symbol.upper().replace('USDT', '')
        req = {
            "method": "subscribe",
            "subscription": {"type": "l2Book", "coin": coin}
        }
        
        async with self.session.ws_connect(url) as ws:
            await ws.send_json(req)
            async for msg in ws:
                if msg.type != aiohttp.WSMsgType.TEXT: continue
                data = ujson.loads(msg.data)
                
                if data.get('channel') == 'l2Book' and 'data' in data:
                    d = data['data']
                    levels = d.get('levels', [[], []])
                    bids = [[x['px'], x['sz']] for x in levels[0]]
                    asks = [[x['px'], x['sz']] for x in levels[1]]
                    await self.broadcast('Hyperliquid', symbol, bids, asks)

    async def run_paradex(self, symbol):
        url = "wss://ws.api.prod.paradex.trade/v1"
        s = symbol.upper().replace('M', '')
        if '-' in s:
             if not s.endswith('PERP'): s = re.sub(r'-USDT$|-USD$', '-USD-PERP', s)
        elif s.endswith('USDT'): s = s.replace('USDT', '-USD-PERP')
        elif s.endswith('USD'): s = s.replace('USD', '-USD-PERP')
        else:
             m = re.match(r'^([A-Z]+)(USDT|USD|PERP)?$', s)
             if m: s = f"{m.group(1)}-USD-PERP"
        
        market = s
        req = {
            "jsonrpc": "2.0",
            "method": "subscribe",
            "params": {"channel": f"order_book.{market}"},
            "id": int(time.time())
        }

        async with self.session.ws_connect(url) as ws:
            await ws.send_json(req)
            async for msg in ws:
                if msg.type != aiohttp.WSMsgType.TEXT: continue
                data = ujson.loads(msg.data)
                
                if 'params' in data and 'data' in data['params']:
                    payload = data['params']['data']
                    
                    raw_bids = payload.get('inserts') or payload.get('updates') or payload.get('bids') or []
                    raw_asks = payload.get('deletes') or payload.get('asks') or [] 

                    def fmt(arr):
                        if not arr: return []
                        return [[x.get('price', x.get('px')), x.get('size', x.get('sz'))] for x in arr]

                    await self.broadcast('Paradex', symbol, fmt(raw_bids), fmt(raw_asks))

    async def run_kucoin(self, symbol):
        token_url = "https://api-futures.kucoin.com/api/v1/bullet-public"
        try:
            async with self.session.post(token_url) as resp:
                res = await resp.json()
                if str(res.get('code')) != "200000":
                    logger.error(f"Kucoin token error: {res}")
                    return
                
                token = res['data']['token']
                endpoint = res['data']['instanceServers'][0]['endpoint']
                
                ws_url = f"{endpoint}?token={token}&connectId={int(time.time() * 1000)}"
        except Exception as e:
            logger.error(f"Kucoin HTTP error: {e}")
            return

        topic = f"/contractMarket/level2Depth5:{symbol.upper()}M" 
        
        async with self.session.ws_connect(ws_url) as ws:
            sub_msg = {
                "id": int(time.time() * 1000),
                "type": "subscribe",
                "topic": topic,
                "response": True
            }
            await ws.send_json(sub_msg)
            
            ping_interval = 15 
            last_ping = time.time()

            async for msg in ws:
                if time.time() - last_ping > ping_interval:
                    await ws.send_json({"id": int(time.time()*1000), "type": "ping"})
                    last_ping = time.time()

                if msg.type != aiohttp.WSMsgType.TEXT: continue
                data = ujson.loads(msg.data)
                
                if data.get('type') == 'message' and 'data' in data:
                    d = data['data']
                    await self.broadcast('Kucoin', symbol, d.get('bids'), d.get('asks'))