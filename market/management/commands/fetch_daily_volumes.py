from datetime import date, datetime

from django.core.management.base import BaseCommand

from market.services import save_daily_volumes


class Command(BaseCommand):
    help = "Загрузить tickers Bybit (linear) и сохранить объёмы на указанную дату (по умолчанию сегодня UTC)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            type=str,
            default=None,
            help="Дата YYYY-MM-DD (по умолчанию сегодня UTC).",
        )

    def handle(self, *args, **options):
        date_str = options.get("date")
        if date_str:
            try:
                day = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                self.stderr.write(self.style.ERROR(f"Неверный формат даты: {date_str}. Используйте YYYY-MM-DD."))
                return
        else:
            day = date.today()
        try:
            count = save_daily_volumes(day)
            self.stdout.write(self.style.SUCCESS(f"Сохранено записей: {count} на дату {day}."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Ошибка: {e}"))
            raise
