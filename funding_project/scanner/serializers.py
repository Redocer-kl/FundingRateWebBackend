from rest_framework import serializers
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Favorite, Asset, Exchange, FundingRate, Ticker, ArbitragePosition, UserExchangeCredential, ParadexAgent

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
    latest_funding = serializers.SerializerMethodField()
    symbol = serializers.CharField()

    class Meta:
        model = Ticker
        fields = ['exchange', 'symbol', 'last_price', 'latest_funding']

    def get_latest_funding(self, obj):
        rate = obj.funding_rates.order_by('-timestamp').first()
        if rate:
            return FundingRateSerializer(rate).data
        return None
    

class ArbitragePositionSerializer(serializers.ModelSerializer):
    long_ticker = TickerDetailSerializer(read_only=True)
    short_ticker = TickerDetailSerializer(read_only=True)

    long_exchange = serializers.CharField(write_only=True)
    long_symbol = serializers.CharField(write_only=True)
    short_exchange = serializers.CharField(write_only=True)
    short_symbol = serializers.CharField(write_only=True)

    class Meta:
        model = ArbitragePosition
        fields = [
            'id', 'long_ticker', 'short_ticker', 
            'long_exchange', 'long_symbol', 
            'short_exchange', 'short_symbol', 
            'amount', 
            'long_entry_target', 'long_exit_target',
            'short_entry_target', 'short_exit_target',
            'status', 'created_at'
        ]

    def _get_ticker(self, exchange_name, symbol_str):
        from django.db.models import Q
        base_symbol = symbol_str.replace('USDT', '')
        
        ticker = Ticker.objects.filter(exchange__name__iexact=exchange_name).filter(
            Q(symbol__iexact=symbol_str) | 
            Q(symbol__iexact=base_symbol) |
            Q(original_symbol__iexact=symbol_str)
        ).first()
        
        if not ticker:
            raise serializers.ValidationError(f"Тикер {symbol_str} не найден на бирже {exchange_name}")
        return ticker

    def create(self, validated_data):
        l_ex = validated_data.pop('long_exchange')
        l_sym = validated_data.pop('long_symbol')
        s_ex = validated_data.pop('short_exchange')
        s_sym = validated_data.pop('short_symbol')
        
        long_ticker = self._get_ticker(l_ex, l_sym)
        short_ticker = self._get_ticker(s_ex, s_sym)

        position = ArbitragePosition.objects.create(
            user=self.context['request'].user,
            long_ticker=long_ticker,
            short_ticker=short_ticker,
            **validated_data
        )
        return position
    

class UserExchangeCredentialSerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(write_only=True)
    api_secret = serializers.CharField(write_only=True)
    passphrase = serializers.CharField(write_only=True, required=False, allow_blank=True)
    private_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    exchange_name = serializers.SlugRelatedField(
        slug_field='name', 
        queryset=Exchange.objects.all(), 
        source='exchange', 
        write_only=True
    )
    display_name = serializers.CharField(source='exchange.name', read_only=True)

    masked_key = serializers.SerializerMethodField()

    class Meta:
        model = UserExchangeCredential
        fields = [
            'exchange_name',
            'display_name',  
            'api_key', 'api_secret', 'passphrase', 'private_key',
            'masked_key', 'is_valid', 'created_at', 'error_message'
        ]
        read_only_fields = ['id', 'created_at', 'is_valid', 'error_message']

    def get_masked_key(self, obj):
        try:
            keys = obj.get_keys()
            real_key = keys.get('apiKey')
            if real_key and len(real_key) > 4:
                return f"****{real_key[-4:]}"
            return "****"
        except:
            return "Error decrypting"
        

class ParadexAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParadexAgent
        fields = ['stark_public_key', 'is_approved', 'created_at']
        read_only_fields = ['stark_public_key', 'is_approved', 'created_at']