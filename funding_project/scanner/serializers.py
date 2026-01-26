from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Favorite, Asset, Exchange, FundingRate, Ticker

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class FavoriteSerializer(serializers.ModelSerializer):
    asset_symbol = serializers.ReadOnlyField(source='asset.symbol')
    exchange_name = serializers.ReadOnlyField(source='exchange.name')

    class Meta:
        model = Favorite
        fields = ('id', 'asset', 'exchange', 'asset_symbol', 'exchange_name')

class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ['symbol', 'image_url', 'market_cap', 'volume_24h']

class ExchangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exchange
        fields = ['id', 'name']

class FundingRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundingRate
        fields = ['timestamp', 'rate', 'apr', 'period_hours']

class TickerDetailSerializer(serializers.ModelSerializer):
    exchange = serializers.ReadOnlyField(source='exchange.name')
    # Для деталей конкретной монеты нам нужны последние ставки
    latest_funding = serializers.SerializerMethodField()

    class Meta:
        model = Ticker
        fields = ['exchange', 'last_price', 'latest_funding']

    def get_latest_funding(self, obj):
        rate = obj.funding_rates.order_by('-timestamp').first()
        if rate:
            return FundingRateSerializer(rate).data
        return None