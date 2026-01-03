import os
from celery import Celery

# Указываем Django настройки по умолчанию
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'funding_project.settings')

app = Celery('funding_project')

# Используем настройки из settings.py, начинающиеся с CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находить tasks.py в приложениях
app.autodiscover_tasks()