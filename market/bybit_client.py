"""
Публичный клиент Bybit API v5 (без ключей).
Запросы: tickers, klines. Ретраи при 429/5xx, логирование.
"""
import logging
import time
from decimal import Decimal
from typing import Any

import requests

logger = logging.getLogger(__name__)

BYBIT_BASE_URL = "https://api.bybit.com"
BYBIT_TESTNET_URL = "https://api-testnet.bybit.com"
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0


def _request(
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    base_url = base_url or BYBIT_BASE_URL
    url = f"{base_url.rstrip('/')}{path}"
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.request(
                method,
                url,
                params=params,
                timeout=30,
            )
            if resp.status_code == 429 or resp.status_code >= 500:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF ** attempt)
                    continue
            resp.raise_for_status()
            data = resp.json()
            if data.get("retCode") != 0:
                logger.warning("Bybit API retCode=%s retMsg=%s", data.get("retCode"), data.get("retMsg"))
            return data
        except requests.RequestException as e:
            logger.warning("Bybit request attempt %s failed: %s", attempt + 1, e)
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(RETRY_BACKOFF ** attempt)
    return {}


def get_tickers(category: str = "linear", base_url: str | None = None) -> list[dict[str, Any]]:
    """
    Список тикеров по категории (linear, spot, inverse).
    Bybit возвращает все пары одним запросом; при >500 linear может потребоваться обход.
    """
    data = _request(
        "GET",
        "/v5/market/tickers",
        params={"category": category},
        base_url=base_url,
    )
    result = data.get("result") or {}
    return result.get("list") or []


def get_klines(
    symbol: str,
    interval: str,
    start_ms: int,
    end_ms: int,
    category: str = "linear",
    limit: int = 1000,
    base_url: str | None = None,
) -> list[list]:
    """
    Свечи по символу. Интервал: 1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M.
    Возвращает список массивов [startTime, open, high, low, close, volume, turnover].
    """
    data = _request(
        "GET",
        "/v5/market/kline",
        params={
            "category": category,
            "symbol": symbol.upper(),
            "interval": str(interval),
            "start": start_ms,
            "end": end_ms,
            "limit": min(limit, 1000),
        },
        base_url=base_url,
    )
    result = data.get("result") or {}
    raw = result.get("list") or []
    return [list(row) for row in raw]


def parse_kline_row(row: list) -> dict[str, Any]:
    """Парсит один элемент из get_klines: [startTime, open, high, low, close, volume, turnover]."""
    try:
        return {
            "start_time_ms": int(row[0]),
            "open": Decimal(str(row[1])),
            "high": Decimal(str(row[2])),
            "low": Decimal(str(row[3])),
            "close": Decimal(str(row[4])),
            "volume": Decimal(str(row[5])),
            "turnover": Decimal(str(row[6])) if len(row) > 6 and row[6] else None,
        }
    except (IndexError, TypeError, ValueError) as e:
        logger.warning("Parse kline row failed: %s row=%s", e, row)
        raise
