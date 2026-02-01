from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model


User = get_user_model()

class Exchange(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    api_url = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class Asset(models.Model):
    symbol = models.CharField(max_length=20, unique=True, help_text="Универсальный символ (BTC, ETH)")
    
    market_cap = models.DecimalField(max_digits=25, decimal_places=2, null=True, blank=True)
    volume_24h = models.DecimalField(max_digits=25, decimal_places=2, null=True, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    
    coingecko_id = models.CharField(max_length=100, null=True, blank=True, unique=True)

    def __str__(self):
        return self.symbol

class Ticker(models.Model):
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE, related_name='tickers')
    
    asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickers')
    
    symbol = models.CharField(max_length=50)     
    original_symbol = models.CharField(max_length=100) 

    last_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    

    class Meta:
        unique_together = ('exchange', 'symbol')

    def save(self, *args, **kwargs):
        if not self.asset_id:
            clean_symbol = self.symbol.upper().replace('1000', '').replace('K', '').split('-')[0]
            
            asset_obj, _ = Asset.objects.get_or_create(symbol=clean_symbol)
            self.asset = asset_obj
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.symbol} @ {self.exchange.name}"

class FundingRate(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name='funding_rates')
    timestamp = models.DateTimeField(db_index=True)
    rate = models.DecimalField(max_digits=20, decimal_places=10)
    period_hours = models.IntegerField(default=1) 
    apr = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

   

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['ticker', 'timestamp']),
        ]
        unique_together = ('ticker', 'timestamp')

    def save(self, *args, **kwargs):
        if self.rate is not None and self.period_hours:
            periods_per_year = (24 / self.period_hours) * 365
            self.apr = float(self.rate) * periods_per_year * 100
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticker.symbol} @ {self.timestamp}: {self.apr}% APR"
    

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, null=True, blank=True)
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'asset', 'exchange')

    def __str__(self):
        target = self.asset.symbol if self.asset else self.exchange.name
        return f"{self.user.username} follows {target}"
    

class ArbitragePosition(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Entry'), # Ждем цены входа
        ('ACTIVE', 'Active'),         # В позиции
        ('CLOSING', 'Closing'),       # В процессе выхода
        ('CLOSED', 'Closed'),         # Завершена
        ('FAILED', 'Failed'),         # Ошибка
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='positions')
    
    long_ticker = models.ForeignKey(Ticker, on_delete=models.PROTECT, related_name='long_positions')
    short_ticker = models.ForeignKey(Ticker, on_delete=models.PROTECT, related_name='short_positions')
    
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0, help_text="Общая сумма позиции в USDT")
    
    long_entry_target = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True, help_text="Цена входа (если пусто - по рынку)")
    long_exit_target = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True, help_text="Тейк профит для лонга")
    
    short_entry_target = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    short_exit_target = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)

    realized_entry_long = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    realized_entry_short = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Arb {self.id}: {self.long_ticker.symbol} vs {self.short_ticker.symbol} ({self.status})"
    