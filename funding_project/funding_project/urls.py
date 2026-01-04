from django.contrib import admin
from django.urls import path
from scanner.views import funding_table, coin_detail, best_opportunities, index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('table/', funding_table, name='funding_table'),
    path('coin/<str:symbol>/', coin_detail, name='coin_detail'),
    path('best/', best_opportunities, name='best_opportunities'),
]