from django.contrib import admin
from market.models import Candle, SelectedTicker, TickerDailyVolume Candle, SelectedTicker, TickerDailyVolume


@admin.register(TickerDailyVolume)
class TickerDailyVolumeAdmin(admin.ModelAdmin):
    list_display = ("date", "symbol", "category", "volume24h", "turnover24h", "last_price")
    list_filter = ("date", "category")
    search_fields = ("symbol",)
    date_hierarchy = "date"
    ordering = ("-date", "symbol")


@admin.register(SelectedTicker)
class SelectedTickerAdmin(admin.ModelAdmin):
    list_display = ("date", "symbol", "created_at")
    list_filter = ("date",)
    search_fields = ("symbol",)
    date_hierarchy = "date"
    ordering = ("date", "symbol")


@admin.register(Candle)
class CandleAdmin(admin.ModelAdmin):
    list_display = ("symbol", "interval", "start_time", "open", "high", "low", "close", "volume")
    list_filter = ("symbol", "interval")
    search_fields = ("symbol",)
    ordering = ("-start_time", "symbol")
