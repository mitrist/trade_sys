# Контракт API OpenClaw: анализ данных и обучение

Документ описывает сценарии работы агента OpenClaw с бэкендом: создание запусков, отправка анализов и сигналов, обратная связь и типы запусков.

**Базовый URL API:** `/api/agent/`

---

## 1. Типы запусков (run_type)

При создании run можно указать тип запуска для фильтрации в интерфейсе:

| Значение    | Описание        |
|------------|------------------|
| `analysis` | Только анализ данных (по умолчанию) |
| `training` | Обучение (дообучение весов, сценарии) |
| `demo`     | Демо-торговля |
| `live`     | Реальная торговля |

Передаётся в теле `POST /api/agent/runs/`: поле `run_type` (опционально).

---

## 2. Сценарий «Анализ данных»

1. **Создать run:**  
   `POST /api/agent/runs/`  
   Тело: `{ "trigger": "manual", "run_type": "analysis", "input_params": { "date": "2025-03-15", "tickers": ["SBER"], "interval": "1d" } }`

2. **Отправить шаги рассуждений и анализы:**  
   `POST /api/agent/runs/<id>/analysis/`  
   Тело: `{ "items": [ { "symbol": "SBER", "analysis_type": "reasoning_step", "content": { ... } }, ... ] }`

3. **Формат шага рассуждения (reasoning_step):**  
   Для записей с `analysis_type: "reasoning_step"` поле `content` должно содержать:
   - `step` (число) — порядковый номер шага
   - `description` (строка) — текст шага
   - `input_data` (объект) — использованные данные (символ, метрики, уровни)
   - `conclusion` (строка) — вывод шага
   - `rule` (строка, опционально) — идентификатор правила из справочника (см. п. 4)

4. **Итоговые анализы:** те же `POST .../analysis/` с типами `volume_anomaly`, `poc_hvn`, `zone_near`, `custom` и своим `content`.

5. **Сигналы (гипотезы):**  
   `POST /api/agent/runs/<id>/signals/`  
   Тело: `{ "items": [ { "symbol", "side", "price_level", "stop_level", "target_level", "reason", "rule", "confidence" }, ... ] }`  
   Поле `rule` — идентификатор правила стратегии (см. п. 4).

6. **Логи:**  
   `POST /api/agent/runs/<id>/logs/`  
   Тело: `{ "items": [ { "level": "info", "message": "...", "source": "..." }, ... ] }`

7. **Завершить run:**  
   `PATCH /api/agent/runs/<id>/`  
   Тело: `{ "status": "success", "summary": "Краткий итог анализа", "finished_at": "2025-03-15T12:00:00Z" }`

---

## 3. Сценарий «Обучение»

1. Создать run с `run_type: "training"`.
2. В `input_params` указать период данных, например: `{ "period_start": "2025-01-01", "period_end": "2025-03-15" }`.
3. Те же шаги: отправка reasoning_step, анализов, сигналов, логов.
4. В `summary` при завершении указать результат обучения, например: «Обновлены веса по N сценариям».

---

## 4. Правила стратегии (rule)

Справочник правил описан в `agent/strategy_rules.json`: поля `id`, `name`, `excerpt` (фрагмент из descr).

Допустимые идентификаторы (примеры):  
`trade_from_level`, `trade_on_return`, `stop_beyond_zone`, `filter_near_zone`, `poc_hvn`.

В анализе (в т.ч. в `content.reasoning_step`) и в сигнале поле `rule` — строка с таким `id`. В UI отображается название правила и подсказка (excerpt).

---

## 5. Обратная связь (feedback)

**Назначение:** пользователь корректирует рассуждения агента; OpenClaw может читать feedback для дообучения.

- **GET** `/api/agent/runs/<id>/feedback/` — список обратной связи по run (тело ответа — массив объектов с полями `id`, `run`, `signal`, `feedback_type`, `comment`, `user`, `created_at`).

- **POST** `/api/agent/runs/<id>/feedback/` — создать отзыв.  
  Тело: `{ "signal_id": 123 }` или `{ "signal": 123 }` — привязка к сигналу; без `signal_id`/`signal` — отзыв на весь run.  
  Обязательно: `feedback_type` — одно из `correction`, `override`, `approve`; опционально: `comment` (текст).

**Рекомендация для OpenClaw:** периодически запрашивать `GET .../runs/<id>/feedback/` по завершённым runs и учитывать комментарии и тип (коррекция/одобрение/отклонение) при дообучении или в следующих запусках.

---

## 6. Краткая сводка эндпоинтов

| Метод | URL | Назначение |
|-------|-----|------------|
| GET   | `/api/agent/runs/` | Список запусков |
| POST  | `/api/agent/runs/` | Создать run (trigger, input_params, run_type) |
| GET   | `/api/agent/runs/<id>/` | Детали run |
| PATCH | `/api/agent/runs/<id>/` | Обновить status, summary, finished_at |
| POST  | `/api/agent/runs/<id>/analysis/` | Добавить анализы (items: symbol, analysis_type, content) |
| POST  | `/api/agent/runs/<id>/signals/` | Добавить сигналы (items: symbol, side, reason, rule, …) |
| POST  | `/api/agent/runs/<id>/logs/` | Добавить логи |
| GET   | `/api/agent/runs/<id>/feedback/` | Список обратной связи |
| POST  | `/api/agent/runs/<id>/feedback/` | Создать обратную связь |
