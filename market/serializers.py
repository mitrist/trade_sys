from rest_framework import serializers

from market.models import Candle, SelectedTicker, TickerDailyVolume


class SelectedTickerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelectedTicker
        fields = ("date", "symbol", "created_at")


class TickerDailyVolumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TickerDailyVolume
        fields = (
            "date",
            "symbol",
            "category",
            "volume24h",
            "turnover24h",
            "high_price24h",
            "low_price24h",
            "last_price",
        )


class CandleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candle
        fields = (
            "symbol",
            "interval",
            "start_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "turnover",
        )
