from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views, api_views

api_urlpatterns = [
    #Stats
    path('stats/', api_views.ScannerStatsView.as_view(), name='api-stats'),

    # CoinData
    path('funding-table/', api_views.FundingTableAPIView.as_view(), name='api_funding_table'),
    path('coin-detail/<str:symbol>/', api_views.CoinDetailAPIView.as_view(), name='api_coin_detail'),
    path('best-opportunities/', api_views.BestOpportunitiesAPIView.as_view(), name='api_best_opportunities/'),

    # Auth
    path('register/', api_views.RegisterView.as_view(), name='api_register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User Data
    path('profile/', api_views.ProfileView.as_view(), name='api_profile'),
    path('favorite/toggle/', api_views.ToggleFavoriteView.as_view(), name='api_favorite_toggle'),
]

urlpatterns = [
    path('', views.index, name='index'),
    path('table/', views.funding_table, name='funding_table'),
    path('coin/<str:symbol>/', views.coin_detail, name='coin_detail'),
    path('best/', views.best_opportunities, name='best_opportunities'),

    path('api/', include(api_urlpatterns)),
]