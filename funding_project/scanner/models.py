from django.db import models

class Exchange(models.Model):
    """Справочник бирж (Hyperliquid, Drift, Bitget...)"""
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    api_url = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class Ticker(models.Model):
    """Торговые пары (BTC-USD, ETH-USDT...)"""
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE, related_name='tickers')
    symbol = models.CharField(max_length=50) 
    original_symbol = models.CharField(max_length=100) 

    last_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    class Meta:
        unique_together = ('exchange', 'symbol')

    def __str__(self):
        return f"{self.symbol} ({self.exchange.name})"

class FundingRate(models.Model):
    """
    Исторические данные по фандингу.
    Уникальность определяется биржей, тикером и временем.
    """
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