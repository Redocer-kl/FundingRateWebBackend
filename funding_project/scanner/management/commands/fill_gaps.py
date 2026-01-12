from django.core.management.base import BaseCommand
from django.utils import timezone
from scanner.models import Ticker, FundingRate

from scanner.exchanges.hyperliquid import HyperliquidScanner
from scanner.exchanges.bitget import BitgetScanner
from scanner.exchanges.paradex import ParadexScanner
import time

class Command(BaseCommand):
    help = 'Заполняет пробелы в истории фандинга'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=3, help='Сколько дней назад смотреть')
        parser.add_argument('--exchange', type=str, default='ALL', help='Какую биржу чинить (Hyperliquid, Bitget, Paradex)')

    def handle(self, *args, **options):
        days = options['days']
        target_exchange = options['exchange']
        
        scanners = {
            'Hyperliquid': HyperliquidScanner(),
            'Bitget': BitgetScanner(),
            'Paradex': ParadexScanner(),
        }

        if target_exchange != 'ALL':
            if target_exchange in scanners:
                scanners = {target_exchange: scanners[target_exchange]}
            else:
                self.stdout.write(self.style.ERROR(f'Биржа {target_exchange} не найдена'))
                return

        self.stdout.write(f"Начинаем заполнение пробелов за последние {days} дней...")

        for name, scanner in scanners.items():
            self.stdout.write(f"--- Обработка {name} ---")
            
            tickers = Ticker.objects.filter(exchange__name=name).exclude(original_symbol__isnull=True).exclude(original_symbol__exact='')
            
            total = tickers.count()
            self.stdout.write(f"Найдено {total} валидных тикеров")

            for i, ticker in enumerate(tickers):
                if not ticker.original_symbol:
                    self.stdout.write(self.style.WARNING(f"Пропуск тикера без символа: ID {ticker.id}"))
                    continue

                try:
                    if i % 10 == 0:
                         self.stdout.write(f"[{i}/{total}] Обработка {ticker.original_symbol}...")

                    history = scanner.fetch_funding_history(ticker.original_symbol, lookback_days=days)
                    
                    if not history:
                        time.sleep(0.1) 
                        continue

                    new_records = []
                    for row in history:
                        rate_obj = FundingRate(
                            ticker=ticker,
                            timestamp=row['timestamp'],
                            rate=row['rate'],
                            apr=row['rate'] * (24 / row['period_hours']) * 365 * 100,
                            period_hours=row['period_hours']
                        )
                        new_records.append(rate_obj)

                    FundingRate.objects.bulk_create(new_records, ignore_conflicts=True)
                    
                    if new_records:
                        self.stdout.write(f"✅ {ticker.symbol}: +{len(new_records)} записей")

                    time.sleep(0.2) 

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Ошибка {ticker.symbol}: {e}"))
                    time.sleep(0.5) 

        self.stdout.write(self.style.SUCCESS('Заполнение пробелов завершено!'))