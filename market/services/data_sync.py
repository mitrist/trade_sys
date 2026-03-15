"""
Сохранение данных Bybit в БД: дневные объёмы по всем парам, свечи по символу.
"""
import logging
from datetime import date, datetime
from decimal import Decimal

from django.utils import timezone

from market.bybit_client import get_klines, get_tickers, parse_kline_row
from market.models import Candle, TickerDailyVolume

logger = logging.getLogger(__name__)


def _decimal_or_none(value: str | None) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(value)
    except Exception:
        return None


def save_daily_volumes(day: date) -> int:
    """
    Загружает tickers по category=linear и сохраняет/обновляет TickerDailyVolume на дату day.
    Возвращает количество записей.
    """
    tickers = get_tickers(category="linear")
    created = 0
    for item in tickers:
        try:
            symbol = item.get("symbol")
            if not symbol:
                continue
            volume24h = _decimal_or_none(item.get("volume24h"))
            turnover24h = _decimal_or_none(item.get("turnover24h"))
            high_price24h = _decimal_or_none(item.get("highPrice24h"))
            low_price24h = _decimal_or_none(item.get("lowPrice24h"))
            last_price = _decimal_or_none(item.get("lastPrice"))
            TickerDailyVolume.objects.update_or_create(
                date=day,
                symbol=symbol,
                category="linear",
                defaults={
                    "volume24h": volume24h,
                    "turnover24h": turnover24h,
                    "high_price24h": high_price24h,
                    "low_price24h": low_price24h,
                    "last_price": last_price,
                },
            )
            created += 1
        except Exception as e:
            logger.warning("save_daily_volumes skip symbol=%s: %s", item.get("symbol"), e)
    logger.info("save_daily_volumes date=%s saved %s records", day, created)
    return created


def save_klines_for_symbol(
    symbol: str,
    interval: str,
    start_time: datetime,
    end_time: datetime,
    category: str = "linear",
) -> int:
    """
    Запрашивает klines по диапазону (разбивает на батчи по 1000), парсит и bulk create/update
    в Candle. Уникальность по (symbol, interval, start_time). Возвращает количество сохранённых.
    """
    start_ms = int(start_time.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)
    saved = 0
    current_start = start_ms
    while current_start < end_ms:
        raw = get_klines(
            symbol=symbol,
            interval=interval,
            start_ms=current_start,
            end_ms=end_ms,
            category=category,
            limit=1000,
        )
        if not raw:
            break
        candles_to_upsert = []
        for row in raw:
            try:
                parsed = parse_kline_row(row)
            except Exception:
                continue
            start_ts = parsed["start_time_ms"]
            start_dt = timezone.make_aware(
                datetime.utcfromtimestamp(start_ts / 1000.0),
                timezone=timezone.utc,
            )
            candles_to_upsert.append(
                Candle(
                    symbol=symbol.upper(),
                    interval=str(interval),
                    start_time=start_dt,
                    open=parsed["open"],
                    high=parsed["high"],
                    low=parsed["low"],
                    close=parsed["close"],
                    volume=parsed["volume"],
                    turnover=parsed.get("turnover"),
                )
            )
        for c in candles_to_upsert:
            Candle.objects.update_or_create(
                symbol=c.symbol,
                interval=c.interval,
                start_time=c.start_time,
                defaults={
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                    "turnover": c.turnover,
                },
            )
            saved += 1
        last_ts = int(raw[-1][0])
        if last_ts >= current_start:
            current_start = last_ts + 1
        else:
            break
    logger.info("save_klines_for_symbol symbol=%s interval=%s saved %s", symbol, interval, saved)
    return saved
