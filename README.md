# Торговая система Volume-POC

Сбор данных Bybit (объёмы по парам, свечи по выбранным тикерам), ручной выбор тикеров на день, API для анализа и будущей интеграции с OpenClaw.

## Стек

- Django 4.x, Django REST Framework, SQLite (при необходимости — PostgreSQL)
- Публичное API Bybit v5 (tickers, klines)

## Установка и запуск

1. Клонируй репозиторий и перейди в каталог проекта.
2. Создай виртуальное окружение и установи зависимости:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate  # Linux/macOS
   pip install -r requirements.txt
   ```

3. Переменные окружения (опционально):

   - `SECRET_KEY` — секрет Django (по умолчанию dev-ключ).
   - `DEBUG` — `1` или `0` (по умолчанию `1`).
   - `ALLOWED_HOSTS` — через запятую (по умолчанию `localhost,127.0.0.1`).

4. Миграции и суперпользователь:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. Запуск сервера:

   ```bash
   python manage.py runserver
   ```

- Админка: <http://127.0.0.1:8000/admin/>
- Страница выбора тикеров на день: <http://127.0.0.1:8000/api/select-tickers/> (требуется вход)
- Графики выбранных тикеров (TradingView): <http://127.0.0.1:8000/api/charts/> (требуется вход)
- История объёма по тикеру: <http://127.0.0.1:8000/api/volume-history/> — выбор тикера и график объёма/оборота по дням (требуется вход)
- API (read-only): <http://127.0.0.1:8000/api/selected-tickers/>, `/api/daily-volumes/`, `/api/candles/`

## Команды сбора данных

- **Ежедневные объёмы по всем парам (linear):**

  ```bash
  python manage.py fetch_daily_volumes [--date=YYYY-MM-DD]
  ```

  По умолчанию используется текущая дата (UTC). Результат пишется в `TickerDailyVolume`.

- **Свечи по выбранным тикерам на дату:**

  ```bash
  python manage.py fetch_klines_for_selected [--date=YYYY-MM-DD] [--interval=15] [--days=1]
  ```

  Берёт из `SelectedTicker` тикеры на указанную дату и загружает klines за день (или за несколько дней). Результат пишется в `Candle`.

## Как задать тикеры на день

1. Утром зайди в админку или на страницу **Тикеры на день** (`/api/select-tickers/`).
2. Выбери дату и введи символы через запятую (например `BTCUSDT, ETHUSDT`), нажми «Сохранить».
3. Запусти сбор свечей для этой даты командой `fetch_klines_for_selected` (вручную или по крону).

## API (для OpenClaw и скриптов)

- `GET /api/selected-tickers/?date=YYYY-MM-DD` — список тикеров на день.
- `GET /api/daily-volumes/?date=YYYY-MM-DD&symbol=...` — дневные объёмы (фильтр по дате и опционально по symbol).
- `GET /api/candles/?symbol=...&interval=...&start=...&end=...` — свечи (фильтры по symbol, interval, start, end в ISO формате).

Требуется аутентификация (SessionAuthentication). Для OpenClaw позже можно добавить токен или отдельный ключ.

## Развёртывание на VM (Яндекс и др.)

- ОС: Linux (Ubuntu 22.04), Python 3.10+.
- Установка: виртуальное окружение, `pip install -r requirements.txt` (в него входит gunicorn — ставить через pip в venv, не через `apt`), `python manage.py migrate`, `python manage.py collectstatic`.
- Запуск Gunicorn (обязательно `--bind`, не `--`):
  ```bash
  .venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:8000
  ```
  Проксирование через nginx, HTTPS (Let's Encrypt).
- Переменные: `SECRET_KEY`, `DEBUG=0`, `ALLOWED_HOSTS` с доменом/IP. Чтобы подгрузить `.env` в текущую оболочку: `set -a && source .env && set +a` (или `export $(grep -v '^#' .env | xargs)`).

### Частые проблемы при запуске

- **«That port is already in use»** — порт 8000 занят. Найти процесс: `lsof -i :8000` (или `ss -tlnp | grep 8000`), завершить: `kill <PID>`. Либо запустить на другом порту: `--bind 0.0.0.0:8001`.
- **«Command gunicorn not found»** — ставить gunicorn в виртуальном окружении: `pip install gunicorn` или `pip install -r requirements.txt`, затем вызывать через `./.venv/bin/gunicorn` или активировать venv и запускать `gunicorn`.
- **Загрузка переменных из `.env`** — команда не `.env`, а `source .env` (или `source .env` в bash).

### Крон (рекомендуемое расписание)

- Раз в сутки сохранять объёмы по всем парам:

  ```cron
  10 0 * * * cd /path/to/project && .venv/bin/python manage.py fetch_daily_volumes
  ```

- Раз в сутки (или каждые N часов) собирать свечи по выбранным тикерам за текущий день:

  ```cron
  30 0 * * * cd /path/to/project && .venv/bin/python manage.py fetch_klines_for_selected --interval=15
  ```

Время в кроне — по UTC (или подстрой под свой часовой пояс).

## Документация стратегии

Краткое описание логики Volume-POC: файл [descr.txt](descr.txt) в корне проекта.
