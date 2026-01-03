from django.contrib import admin
from django.urls import path
from scanner.views import funding_table, coin_detail

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', funding_table, name='home'),
    path('coin/<str:symbol>/', coin_detail, name='coin_detail'),
]