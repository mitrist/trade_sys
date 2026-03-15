from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from market.models import SelectedTicker


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
