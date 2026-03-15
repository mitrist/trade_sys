import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from market.models import SelectedTicker, TickerDailyVolume


@login_required
@require_http_methods(["GET", "POST"])
def select_tickers_for_day(request):
    """
    Простая страница: выбор даты и список символов (через запятую).
    Сохраняет SelectedTicker на выбранную дату.
    """
    if request.method == "POST":
        date_str = request.POST.get("date")
        symbols_str = request.POST.get("symbols", "").strip()
        if not date_str:
            return render(
                request,
                "market/select_tickers.html",
                {"error": "Укажите дату.", "symbols": symbols_str},
            )
        try:
            day = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return render(
                request,
                "market/select_tickers.html",
                {"error": "Неверный формат даты (YYYY-MM-DD).", "date": date_str, "symbols": symbols_str},
            )
        symbols = [s.strip().upper() for s in symbols_str.split(",") if s.strip()]
        created = 0
        for symbol in symbols:
            _, created_flag = SelectedTicker.objects.get_or_create(date=day, symbol=symbol)
            if created_flag:
                created += 1
        return render(
            request,
            "market/select_tickers.html",
            {"success": f"Тикеры на {day} сохранены (добавлено новых: {created}).", "date": date_str, "symbols": symbols_str},
        )
    return render(request, "market/select_tickers.html", {})


@login_required
@require_http_methods(["GET"])
def selected_tickers_charts(request):
    """
    Страница с графиками выбранных тикеров (TradingView).
    GET ?date=YYYY-MM-DD — тикеры на эту дату; без date — сегодня.
    """
    date_str = request.GET.get("date")
    if date_str:
        try:
            day = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            day = timezone.now().date()
    else:
        day = timezone.now().date()
    tickers = list(
        SelectedTicker.objects.filter(date=day).order_by("symbol").values_list("symbol", flat=True)
    )
    return render(
        request,
        "market/selected_tickers_charts.html",
        {
            "date": day,
            "date_str": day.strftime("%Y-%m-%d"),
            "tickers": tickers,
            "tickers_json": json.dumps(tickers),
        },
    )


@login_required
@require_http_methods(["GET"])
def volume_history(request):
    """
    Страница выбора тикера и графика истории объёма (по TickerDailyVolume).
    GET ?symbol=BTCUSDT — показать историю объёма по этому тикеру.
    """
    symbols = list(
        TickerDailyVolume.objects.values_list("symbol", flat=True).distinct().order_by("symbol")
    )
    symbol = (request.GET.get("symbol") or "").strip().upper()
    dates = []
    volumes = []
    turnovers = []
    if symbol:
        rows = (
            TickerDailyVolume.objects.filter(symbol=symbol, category="linear")
            .order_by("date")
            .values("date", "volume24h", "turnover24h")
        )
        for r in rows:
            dates.append(r["date"].strftime("%Y-%m-%d"))
            volumes.append(float(r["volume24h"] or 0))
            turnovers.append(float(r["turnover24h"] or 0))
    return render(
        request,
        "market/volume_history.html",
        {
            "symbols": symbols,
            "symbol": symbol or None,
            "dates_json": json.dumps(dates),
            "volumes_json": json.dumps(volumes),
            "turnovers_json": json.dumps(turnovers),
        },
    )
