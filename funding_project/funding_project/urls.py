from django.contrib import admin
from django.urls import path
from scanner.views import funding_table

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', funding_table, name='home'), # Главная страница с таблицей
]