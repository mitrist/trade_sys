from datetime import datetime

from django.utils import timezone
from rest_framework.generics import ListAPIView

from market.models import Candle, SelectedTicker, TickerDailyVolume
from market.serializers import CandleSerializer, SelectedTickerSerializer, TickerDailyVolumeSerializer


class SelectedTickerListAPIView(ListAPIView):
    """
    GET /api/selected-tickers/?date=YYYY-MM-DD — список тикеров на день.
    """
    serializer_class = SelectedTickerSerializer

    def get_queryset(self):
        date_str = self.request.query_params.get("date")
        if not date_str:
            return SelectedTicker.objects.none()
        try:
            day = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return SelectedTicker.objects.none()
        return SelectedTicker.objects.filter(date=day).order_by("symbol")


class DailyVolumeListAPIView(ListAPIView):
    """
    GET /api/daily-volumes/?date=YYYY-MM-DD&symbol=BTCUSDT — дневные объёмы (фильтр по дате и опционально symbol).
    """
    serializer_class = TickerDailyVolumeSerializer

    def get_queryset(self):
        qs = TickerDailyVolume.objects.all().order_by("-date", "symbol")
        date_str = self.request.query_params.get("date")
        symbol = self.request.query_params.get("symbol", "").strip()
        if date_str:
            try:
                day = datetime.strptime(date_str, "%Y-%m-%d").date()
                qs = qs.filter(date=day)
            except ValueError:
                pass
        if symbol:
            qs = qs.filter(symbol=symbol.upper())
        return qs


class CandleListAPIView(ListAPIView):
    """
    GET /api/candles/?symbol=BTCUSDT&interval=15&start=...&end=... — свечи (фильтры по symbol, interval, start, end).
    """
    serializer_class = CandleSerializer

    def get_queryset(self):
        qs = Candle.objects.all().order_by("symbol", "interval", "start_time")
        symbol = self.request.query_params.get("symbol", "").strip()
        interval = self.request.query_params.get("interval", "").strip()
        start_str = self.request.query_params.get("start")
        end_str = self.request.query_params.get("end")
        if symbol:
            qs = qs.filter(symbol=symbol.upper())
        if interval:
            qs = qs.filter(interval=interval)
        if start_str:
            try:
                start_dt = timezone.make_aware(
                    datetime.fromisoformat(start_str.replace("Z", "+00:00")),
                    timezone=timezone.utc,
                )
                qs = qs.filter(start_time__gte=start_dt)
            except (ValueError, TypeError):
                pass
        if end_str:
            try:
                end_dt = timezone.make_aware(
                    datetime.fromisoformat(end_str.replace("Z", "+00:00")),
                    timezone=timezone.utc,
                )
                qs = qs.filter(start_time__lte=end_dt)
            except (ValueError, TypeError):
                pass
        return qs
