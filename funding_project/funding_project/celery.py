import os
from celery import Celery
from celery.signals import beat_init

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'funding_project.settings')

app = Celery('funding_project')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

@beat_init.connect
def run_tasks_on_startup(sender, **kwargs):
    from scanner.tasks import scan_exchange_task 

    exchanges_to_run = ['Bitget', 'Paradex', 'Hyperliquid', 'Binance', 'Kucoin','CoinEx']
    
    for ex_name in exchanges_to_run:
        scan_exchange_task.delay(ex_name)