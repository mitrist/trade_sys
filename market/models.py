from django.db import models


class TickerDailyVolume(models.Model):
    """Ежедневный снимок объёмов по одной паре (Bybit tickers)."""

    date = models.DateField(db_index=True)
    symbol = models.CharField(max_length=32, db_index=True)
    category = models.CharField(max_length=16, default="linear")
    volume24h = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)
    turnover24h = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)
    high_price24h = models.DecimalField(
        max_digits=24, decimal_places=8, null=True, blank=True
    )
    low_price24h = models.DecimalField(
        max_digits=24, decimal_places=8, null=True, blank=True
    )
    last_price = models.DecimalField(
        max_digits=24, decimal_places=8, null=True, blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["date", "symbol", "category"],
                name="unique_ticker_daily_volume",
            )
        ]
        ordering = ["-date", "symbol"]

    def __str__(self):
        return f"{self.symbol} {self.date}"


class SelectedTicker(models.Model):
    """Тикеры, выбранные пользователем на день для наблюдения/торговли."""

    date = models.DateField(db_index=True)
    symbol = models.CharField(max_length=32, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["date", "symbol"],
                name="unique_selected_ticker",
            )
        ]
        ordering = ["date", "symbol"]

    def __str__(self):
        return f"{self.symbol} ({self.date})"


class Candle(models.Model):
    """Свечи по выбранным тикерам (OHLCV из Bybit kline)."""

    symbol = models.CharField(max_length=32, db_index=True)
    interval = models.CharField(max_length=8, db_index=True)  # e.g. "15" for 15m
    start_time = models.DateTimeField(db_index=True)
    open = models.DecimalField(max_digits=24, decimal_places=8)
    high = models.DecimalField(max_digits=24, decimal_places=8)
    low = models.DecimalField(max_digits=24, decimal_places=8)
    close = models.DecimalField(max_digits=24, decimal_places=8)
    volume = models.DecimalField(max_digits=24, decimal_places=8)
    turnover = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["symbol", "interval", "start_time"],
                name="unique_candle",
            )
        ]
        ordering = ["symbol", "interval", "start_time"]

    def __str__(self):
        return f"{self.symbol} {self.interval} {self.start_time}"
