import os
from celery import Celery
from celery.signals import beat_init

# Указываем Django настройки по умолчанию
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'funding_project.settings')

app = Celery('funding_project')

# Используем настройки из settings.py, начинающиеся с CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находить tasks.py в приложениях
app.autodiscover_tasks()

@beat_init.connect
def run_tasks_on_startup(sender, **kwargs):
    """
    Эта функция выполнится один раз при старте celery beat.
    Здесь мы вручную запускаем все сканеры, чтобы не ждать crontab.
    """
    print("Celery Beat started: Запускаем первичное сканирование...")
    
    # Импортируем задачу внутри функции, чтобы избежать циклического импорта
    from scanner.tasks import scan_exchange_task 
    
    # Список бирж, которые нужно запустить сразу
    exchanges_to_run = ['EdgeX','Hyperliquid', 'Bitget'] #  'Apex', 'Paradex',  'Lighter'
    
    for ex_name in exchanges_to_run:
        scan_exchange_task.delay(ex_name)