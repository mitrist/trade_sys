from django.conf import settings
from django.db import models


class AgentRun(models.Model):
    """Один запуск агента (OpenClaw)."""

    STATUS_CHOICES = [
        ("running", "Выполняется"),
        ("success", "Успех"),
        ("failed", "Ошибка"),
    ]
    TRIGGER_CHOICES = [
        ("cron", "По расписанию"),
        ("manual", "Вручную"),
    ]
    RUN_TYPE_CHOICES = [
        ("analysis", "Анализ"),
        ("training", "Обучение"),
        ("demo", "Демо"),
        ("live", "Live"),
    ]

    started_at = models.DateTimeField(auto_now_add=True)
    run_type = models.CharField(
        max_length=16, choices=RUN_TYPE_CHOICES, default="analysis", blank=True
    )
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="running")
    trigger = models.CharField(max_length=16, choices=TRIGGER_CHOICES, default="manual")
    input_params = models.JSONField(default=dict, blank=True)
    summary = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Run {self.pk} ({self.started_at})"


class AgentAnalysis(models.Model):
    """Один фрагмент анализа за запуск (аномалия объёма, POC/HVN, зона и т.д.)."""

    ANALYSIS_TYPE_CHOICES = [
        ("reasoning_step", "Шаг рассуждения"),
        ("volume_anomaly", "Аномалия объёма"),
        ("poc_hvn", "POC/HVN"),
        ("zone_near", "Рядом с зоной"),
        ("custom", "Прочее"),
    ]

    run = models.ForeignKey(AgentRun, on_delete=models.CASCADE, related_name="analyses")
    symbol = models.CharField(max_length=32, blank=True)
    analysis_type = models.CharField(max_length=32, choices=ANALYSIS_TYPE_CHOICES, default="custom")
    content = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "Agent analyses"

    def __str__(self):
        return f"{self.run_id} / {self.symbol} / {self.analysis_type}"


class AgentSignal(models.Model):
    """Одно решение/сигнал агента (вход, выход, стоп)."""

    SIDE_CHOICES = [
        ("buy", "Покупка"),
        ("sell", "Продажа"),
        ("hold", "Удержание"),
    ]

    run = models.ForeignKey(AgentRun, on_delete=models.CASCADE, related_name="signals")
    symbol = models.CharField(max_length=32)
    side = models.CharField(max_length=8, choices=SIDE_CHOICES)
    price_level = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)
    stop_level = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)
    target_level = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)
    reason = models.TextField(blank=True)
    rule = models.CharField(max_length=64, blank=True, help_text="Идентификатор правила стратегии (см. strategy_rules.json)")
    confidence = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.run_id} / {self.symbol} / {self.side}"


class AgentFeedback(models.Model):
    """Обратная связь пользователя по run или по конкретному сигналу (для коррекции рассуждений)."""

    FEEDBACK_TYPE_CHOICES = [
        ("correction", "Коррекция"),
        ("override", "Отклонить"),
        ("approve", "Одобрить"),
    ]

    run = models.ForeignKey(AgentRun, on_delete=models.CASCADE, related_name="feedbacks")
    signal = models.ForeignKey(
        AgentSignal, on_delete=models.CASCADE, null=True, blank=True, related_name="feedbacks"
    )
    feedback_type = models.CharField(max_length=16, choices=FEEDBACK_TYPE_CHOICES)
    comment = models.TextField(blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="agent_feedbacks"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Feedback {self.pk} run={self.run_id} type={self.feedback_type}"


class AgentLog(models.Model):
    """Одна запись лога запуска агента."""

    LEVEL_CHOICES = [
        ("debug", "Debug"),
        ("info", "Info"),
        ("warning", "Warning"),
        ("error", "Error"),
    ]

    run = models.ForeignKey(AgentRun, on_delete=models.CASCADE, related_name="logs")
    level = models.CharField(max_length=16, choices=LEVEL_CHOICES, default="info")
    message = models.TextField()
    source = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.run_id} [{self.level}] {self.message[:50]}"
