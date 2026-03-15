from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from market.models import SelectedTicker
from market.services import save_klines_for_symbol


class Command(BaseCommand):
    help = (
        "По выбранным тикерам на дату запросить klines за день (или за последние N дней) и сохранить в Candle."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            type=str,
            default=None,
            help="Дата YYYY-MM-DD (по умолчанию сегодня UTC).",
        )
        parser.add_argument(
            "--interval",
            type=str,
            default="15",
            help="Интервал свечей: 1, 5, 15, 30, 60 и т.д. (по умолчанию 15).",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=1,
            help="Сколько дней истории загружать от указанной даты (по умолчанию 1).",
        )

    def handle(self, *args, **options):
        date_str = options.get("date")
        interval = options.get("interval")
        days = options.get("days")
        if date_str:
            try:
                day = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                self.stderr.write(self.style.ERROR(f"Неверный формат даты: {date_str}. Используйте YYYY-MM-DD."))
                return
        else:
            day = timezone.now().date()
        symbols = list(
            SelectedTicker.objects.filter(date=day).values_list("symbol", flat=True).distinct()
        )
        if not symbols:
            self.stdout.write(self.style.WARNING(f"Нет выбранных тикеров на дату {day}."))
            return
        end_dt = timezone.make_aware(
            datetime.combine(day, datetime.min.time()) + timedelta(days=days),
            timezone=timezone.utc,
        )
        start_dt = timezone.make_aware(
            datetime.combine(day, datetime.min.time()),
            timezone=timezone.utc,
        )
        total = 0
        for symbol in symbols:
            try:
                count = save_klines_for_symbol(symbol, interval, start_dt, end_dt)
                total += count
                self.stdout.write(f"  {symbol}: сохранено свечей {count}")
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  {symbol}: ошибка {e}"))
        self.stdout.write(self.style.SUCCESS(f"Всего сохранено свечей: {total}."))
