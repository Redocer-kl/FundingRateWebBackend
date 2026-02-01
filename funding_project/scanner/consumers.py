import ujson
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
import redis.asyncio as redis

class MarketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.redis = redis.from_url(getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0'))
        await self.accept()
        self.active_subscriptions = set()

    async def disconnect(self, close_code):
        for sub_key in self.active_subscriptions:
            exchange, symbol = sub_key.split(':')
            await self.send_command_to_worker('unsubscribe', exchange, symbol)
            
            group_name = f"market_{exchange}_{symbol}".lower()
            await self.channel_layer.group_discard(group_name, self.channel_name)
        
        print(f"🔌 Client disconnected. Cleaned {len(self.active_subscriptions)} subs.")

    async def receive(self, text_data):
        try:
            data = ujson.loads(text_data)
            action = data.get('action')
            exchange = data.get('exchange')
            symbol = data.get('symbol')

            if action == 'subscribe':
                await self.handle_subscribe(exchange, symbol)
            elif action == 'unsubscribe':
                await self.handle_unsubscribe(exchange, symbol)
                
        except Exception as e:
            print(f"Consumer error: {e}")

    async def handle_subscribe(self, exchange, symbol):
        group_name = f"market_{exchange}_{symbol}".lower()
        sub_key = f"{exchange}:{symbol}"

        await self.channel_layer.group_add(group_name, self.channel_name)
        self.active_subscriptions.add(sub_key)

        await self.send_command_to_worker('subscribe', exchange, symbol)

    async def handle_unsubscribe(self, exchange, symbol):
        group_name = f"market_{exchange}_{symbol}".lower()
        sub_key = f"{exchange}:{symbol}"

        await self.channel_layer.group_discard(group_name, self.channel_name)
        if sub_key in self.active_subscriptions:
            self.active_subscriptions.remove(sub_key)

        await self.send_command_to_worker('unsubscribe', exchange, symbol)

    async def send_command_to_worker(self, action, exchange, symbol):
        payload = {
            "action": action,
            "exchange": exchange,
            "symbol": symbol
        }
        await self.redis.publish('cmd:market_data', ujson.dumps(payload))

    async def market_update(self, event):
        await self.send(text_data=ujson.dumps(event['data']))