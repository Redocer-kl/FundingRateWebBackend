from django.core.management.base import BaseCommand
from scanner.tasks import scan_hyperliquid_task

class Command(BaseCommand):
    help = 'Запуск сканирования вручную'

    def handle(self, *args, **options):
        self.stdout.write("Запуск задачи через команду...")
        result = scan_hyperliquid_task() # Вызываем функцию напрямую (синхронно)
        self.stdout.write(str(result))