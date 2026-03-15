import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from django.db.models import Max, Q
from django.core.paginator import Paginator

from market.models import SelectedTicker, TickerDailyVolume

INSTRUMENTS_ORDER_FIELDS = {
    "symbol": "symbol",
    "rating": "symbol",  # rank by current order
    "price": "last_price",
    "change": "last_price",  # no field, fallback
    "cap": "turnover24h",
    "volume": "turnover24h",
    "circ": "volume24h",
    "volcap": "turnover24h",
    "social": "symbol",
    "category": "symbol",
    "tech": "symbol",
}


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


@login_required
@require_http_methods(["GET"])
def instruments_table(request):
    """
    Таблица инструментов (снимок TickerDailyVolume за последнюю дату).
    Сортировка по каждому столбцу: ?order=field&sort=asc|desc.
    Поиск: ?q=BTC
    """
    # Последняя дата, по которой есть данные
    latest_date = TickerDailyVolume.objects.aggregate(Max("date"))["date__max"]
    if not latest_date:
        return render(
            request,
            "market/instruments_table.html",
            {"rows": [], "total": 0, "date": None, "order": "turnover24h", "sort": "desc", "q": ""},
        )
    qs = TickerDailyVolume.objects.filter(date=latest_date, category="linear")
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(Q(symbol__icontains=q))
    order_key = request.GET.get("order") or "turnover24h"
    order_field = INSTRUMENTS_ORDER_FIELDS.get(order_key, "turnover24h")
    sort_dir = request.GET.get("sort") or "desc"
    if sort_dir == "asc":
        qs = qs.order_by(order_field, "symbol")
    else:
        qs = qs.order_by(f"-{order_field}", "symbol")
    paginator = Paginator(qs, 100)
    page_num = request.GET.get("page", 1)
    page = paginator.get_page(page_num)
    def _fmt_vol(x):
        if x >= 1e12:
            return f"{x / 1e12:.2f} T USD"
        if x >= 1e9:
            return f"{x / 1e9:.2f} B USD"
        if x >= 1e6:
            return f"{x / 1e6:.0f} M USD"
        return f"{x:,.2f} USD"

    rows = []
    for rank, row in enumerate(page.object_list, start=(page.number - 1) * paginator.per_page + 1):
        last = float(row.last_price or 0)
        vol = float(row.volume24h or 0)
        turn = float(row.turnover24h or 0)
        high = float(row.high_price24h or 0)
        low = float(row.low_price24h or 0)
        change_pct = ((last - low) / low * 100) if low else None
        rows.append({
            "rank": rank,
            "symbol": row.symbol,
            "last_price": last,
            "change_pct": change_pct,
            "turnover24h": turn,
            "volume24h": vol,
            "turnover_display": _fmt_vol(turn),
        })
    return render(
        request,
        "market/instruments_table.html",
        {
            "rows": rows,
            "total": paginator.count,
            "date": latest_date,
            "order": order_key,
            "sort": sort_dir,
            "q": q,
            "page": page,
        },
    )
