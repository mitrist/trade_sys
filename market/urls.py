from django.urls import path

from market import views
from market.api_views import (
    CandleListAPIView,
    DailyVolumeListAPIView,
    SelectedTickerListAPIView,
)

app_name = "market"
urlpatterns = [
    path("select-tickers/", views.select_tickers_for_day, name="select_tickers"),
    path("selected-tickers/", SelectedTickerListAPIView.as_view(), name="api-selected-tickers"),
    path("daily-volumes/", DailyVolumeListAPIView.as_view(), name="api-daily-volumes"),
    path("candles/", CandleListAPIView.as_view(), name="api-candles"),
]
