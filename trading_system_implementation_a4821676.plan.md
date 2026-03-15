---
name: Trading system implementation
overview: "План реализации торговой системы на Django + DRF: сбор объёмов Bybit в SQLite, ручной выбор тикеров на день через веб, сбор истории по выбранным тикерам и задел API под OpenClaw. Развёртывание на VM в Яндексе."
todos: []
isProject: false
---

# План реализации торговой системы (Volume-POC)

## Контекст

- **Стратегия:** Volume-POC ([descr.txt](c:\Projects\Traiding\descr.txt)) — торговля от зон объёма (POC, HVN, VA), внутридень, только тикеры с аномальным объёмом.
- **Текущий этап:** сбор данных; тикеры на день задаются вручную утром; накопление истории для анализа и последующей интеграции с OpenClaw.
- **Стек:** Django, Django REST Framework, SQLite (с возможностью перехода на PostgreSQL), фронт на старте — админка Django, при необходимости позже — отдельный UI. Размещение — VM в Яндексе.

---

## Архитектура и потоки данных

```mermaid
flowchart LR
  subgraph external [Bybit]
    Tickers[/v5/market/tickers]
    Kline[/v5/market/kline]
  end
  subgraph backend [Django]
    Jobs[Daily jobs]
    Admin[Admin / Web UI]
    API[DRF API]
    DB[(SQLite)]
  end
  subgraph future [Позже]
    OpenClaw[OpenClaw]
  end
  Tickers --> Jobs
  Kline --> Jobs
  Jobs --> DB
  Admin --> DB
  API --> DB
  OpenClaw -.->|"данные, тикеры на день"| API
```



---

## Фаза 1: Основа проекта и модели данных

**1.1 Инициализация Django-проекта**

- Создать виртуальное окружение, зависимости: `Django`, `djangorestframework`, `requests` (для Bybit API). Файл `requirements.txt` в корне.
- Проект Django (например `config`), одно приложение для рыночных данных (например `market`): тикеры, объёмы, свечи, выбор тикеров на день.
- Настройка SQLite в `settings.py`, `DEBUG` и `SECRET_KEY` через переменные окружения.
- Подключить DRF и (опционально) CORS для будущего фронта.

**1.2 Модели (приложение `market`)**

- **TickerDailyVolume** — ежедневный снимок объёмов по одной паре:
  - `date` (DateField), `symbol` (CharField), `category` (CharField, напр. `linear`);
  - `volume24h`, `turnover24h` (DecimalField или FloatField);
  - при желании: `high_price24h`, `low_price24h`, `last_price`;
  - `Meta.unique_together = (date, symbol, category)` или уникальный индекс.
- **SelectedTicker** — тикеры, выбранные пользователем на день:
  - `date` (DateField), `symbol` (CharField), `created_at` (DateTimeField, auto_now_add);
  - уникальность по `(date, symbol)`.
- **Candle** — свечи по выбранным тикерам (для наблюдения и будущего POC/HVN):
  - `symbol`, `interval` (например `15` для 15m), `start_time` (DateTimeField);
  - `open`, `high`, `low`, `close`, `volume`, `turnover`;
  - уникальность по `(symbol, interval, start_time)`.

Миграции после добавления моделей.

**1.3 Справочник символов (опционально)**

- Модель **Symbol** (или кэш из `instruments-info`): `symbol`, `category`, `base_coin`, `quote_coin`, `status` — для валидации и подсказок в админке. Можно заполнять одним скриптом/командой при необходимости.

---

## Фаза 2: Интеграция с Bybit

**2.1 Клиент Bybit (без ключей)**

- Модуль `market.bybit_client` (или `market.services.bybit`): функции/класс для публичных запросов.
- Базовый URL: `https://api.bybit.com` (и опция testnet через настройки).
- Реализовать:
  - `get_tickers(category="linear")` — обход пагинации, если Bybit вернёт не все пары одним запросом (при >500 парах — уточнить по [документации](https://bybit-exchange.github.io/docs/v5/market/tickers) или получать список символов из `instruments-info` и запрашивать батчами).
  - `get_klines(symbol, interval, start, end, limit=1000)` — запрос к `/v5/market/kline`, парсинг массива свечи (startTime, open, high, low, close, volume, turnover).
- Обработка ошибок и ретраи при 429/5xx, логирование в консоль или Django logger.

**2.2 Сохранение данных в БД**

- Сервис/функции в `market.services` (или внутри приложения):
  - **save_daily_volumes(date)** — вызов `get_tickers("linear")`, для каждой записи — создание/обновление `TickerDailyVolume` на переданную `date`. Дата — календарный день (UTC или выбранный часовой пояс в настройках).
  - **save_klines_for_symbol(symbol, interval, start_time, end_time)** — запрос kline, парсинг, bulk create/update в `Candle` (избегать дубликатов по `symbol, interval, start_time`).

---

## Фаза 3: Ежедневный сбор и сбор по выбранным тикерам

**3.1 Ежедневное сохранение объёмов по всем парам**

- Management-команда: `python manage.py fetch_daily_volumes [--date=YYYY-MM-DD]` (по умолчанию — сегодня UTC).
- Внутри: вызов `save_daily_volumes(date)`. Запуск по крону/Task Scheduler на VM в заданное время (например 00:10 UTC).

**3.2 Сбор свечей по выбранным тикерам**

- Management-команда: `python manage.py fetch_klines_for_selected [--date=YYYY-MM-DD] [--interval=15]`.
- Логика: из `SelectedTicker` выбрать все тикеры на указанную дату; для каждого запросить klines за этот день (или за последние N дней для накопления истории); вызвать `save_klines_for_symbol`. Учесть лимит 1000 свечей на запрос — разбивать по диапазонам `start/end`.

**3.3 Расписание (рекомендация для VM)**

- Крон: раз в сутки `fetch_daily_volumes`; раз в сутки или каждые N часов `fetch_klines_for_selected` за текущий день (и при необходимости за вчера), чтобы по выбранным тикерам накапливалась история.

---

## Фаза 4: Веб-интерфейс для выбора тикеров на день

**4.1 Админка Django**

- Зарегистрировать модели в `admin.py`: `TickerDailyVolume`, `SelectedTicker`, `Candle`.
- Для `SelectedTicker`: фильтр по дате, поиск по символу; возможность добавлять/удалять записи (тикеры на выбранную дату).
- Для `TickerDailyVolume`: фильтр по дате и символу, просмотр объёмов (для ручной проверки аномалий и выбора тикеров).

**4.2 Удобство «утром задаю тикеры»**

- Либо отдельная простая страница (Django template + форма): выбор даты, поле «символы» (через запятую или мультиселект), кнопка «Сохранить» — создаёт/обновляет `SelectedTicker` на эту дату. View вызывает тот же сервис/модель, что и админка.
- Либо ограничиться админкой: фильтр по дате «сегодня», добавление нескольких записей `SelectedTicker` с одной датой. Решение оставить только админку или добавить страницу — на твоё усмотрение; в плане заложить «админка обязательно, отдельная страница — опционально».

---

## Фаза 5: API для данных и будущего OpenClaw

**5.1 DRF эндпоинты (read-only для старта)**

- **Список тикеров на день:** `GET /api/selected-tickers/?date=YYYY-MM-DD` — возврат символов (и при необходимости даты) из `SelectedTicker`.
- **Дневные объёмы:** `GET /api/daily-volumes/?date=...&symbol=...` — выборка из `TickerDailyVolume` (для построения базы аномалий и для агента).
- **Свечи:** `GET /api/candles/?symbol=...&interval=...&start=...&end=...` — выборка из `Candle` (для обучения и анализа OpenClaw).
- **Список символов (если есть модель Symbol):** `GET /api/symbols/` — для валидации и подсказок.

**5.2 Аутентификация и права**

- Для внутреннего использования на VM: можно начать с SessionAuthentication + IsAuthenticated или с токен-аутентификации (DRF TokenAuthentication). Для OpenClaw позже — отдельный API-ключ или сервис-аккаунт с ограниченными правами (только чтение данных и, в будущем, отправка сигналов).

---

## Фаза 6: Развёртывание на VM в Яндексе

- ОС: Linux (Ubuntu 22.04 или аналог). Python 3.10+, виртуальное окружение, установка зависимостей из `requirements.txt`.
- Статика: `collectstatic`, отдача через nginx (или встроенный сервер для минимального варианта).
- Запуск: gunicorn + systemd (или supervisor). Nginx как reverse proxy, HTTPS (Let's Encrypt).
- Переменные окружения: `SECRET_KEY`, `DEBUG=False`, при необходимости `DATABASE_URL` при переходе на PostgreSQL.
- Крон для `fetch_daily_volumes` и `fetch_klines_for_selected` по расписанию.
- Документация в README: как поднять проект, как запустить команды, как добавить тикеры на день и где смотреть данные.

---

## Фаза 7 (позже): OpenClaw и торговля

- Не реализовывать в первой итерации; заложить в архитектуре:
  - OpenClaw как клиент твоего API: получает тикеры на день, дневные объёмы, свечи; отправляет сигналы/решения в бэкенд.
  - Исполнение ордеров на Bybit — централизованно через Django (отдельный сервис/воркер с ключами в env), не с машины OpenClaw.
- Отдельные задачи на будущее: модели для сигналов/ордеров, эндпоинты приёма решений от агента, логирование, ограничения риска (макс. объём, стопы из [descr.txt](c:\Projects\Traiding\descr.txt)).

---

## Порядок выполнения и артефакты


| Шаг | Действие                                                   | Результат                           |
| --- | ---------------------------------------------------------- | ----------------------------------- |
| 1   | Django + DRF + приложение `market`, модели, миграции       | Структура проекта, таблицы в SQLite |
| 2   | Bybit-клиент, save_daily_volumes, save_klines              | Модуль запросов и сохранения        |
| 3   | Команды fetch_daily_volumes и fetch_klines_for_selected    | Ручной и крон-запуск сбора          |
| 4   | Регистрация в админке, опционально страница выбора тикеров | Утренний ввод тикеров на день       |
| 5   | DRF-эндпоинты для selected-tickers, daily-volumes, candles | API для просмотра и для OpenClaw    |
| 6   | README, развёртывание на VM, крон                          | Работающая система на VM            |


После этого у тебя будет: ежедневно заполняемая история объёмов по всем парам, ручной выбор тикеров на день, накопление свечей по выбранным тикерам и API для анализа и последующей интеграции с OpenClaw.