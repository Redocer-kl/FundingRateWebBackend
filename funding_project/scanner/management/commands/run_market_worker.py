from django.core.management.base import BaseCommand
import asyncio
from scanner.services.market_data_worker import MarketStreamManager

class Command(BaseCommand):
    help = 'Starts the Market Data Stream Worker'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Market Stream Worker...'))
        manager = MarketStreamManager()
        try:
            asyncio.run(manager.start())
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('Worker stopped'))