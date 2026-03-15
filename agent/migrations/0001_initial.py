from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name="AgentRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(choices=[("running", "Выполняется"), ("success", "Успех"), ("failed", "Ошибка")], default="running", max_length=16)),
                ("trigger", models.CharField(choices=[("cron", "По расписанию"), ("manual", "Вручную")], default="manual", max_length=16)),
                ("input_params", models.JSONField(blank=True, default=dict)),
                ("summary", models.TextField(blank=True)),
            ],
            options={
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="AgentAnalysis",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("symbol", models.CharField(blank=True, max_length=32)),
                ("analysis_type", models.CharField(choices=[("volume_anomaly", "Аномалия объёма"), ("poc_hvn", "POC/HVN"), ("zone_near", "Рядом с зоной"), ("custom", "Прочее")], default="custom", max_length=32)),
                ("content", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="analyses", to="agent.agentrun")),
            ],
            options={
                "ordering": ["created_at"],
                "verbose_name_plural": "Agent analyses",
            },
        ),
        migrations.CreateModel(
            name="AgentSignal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("symbol", models.CharField(max_length=32)),
                ("side", models.CharField(choices=[("buy", "Покупка"), ("sell", "Продажа"), ("hold", "Удержание")], max_length=8)),
                ("price_level", models.DecimalField(blank=True, decimal_places=8, max_digits=24, null=True)),
                ("stop_level", models.DecimalField(blank=True, decimal_places=8, max_digits=24, null=True)),
                ("target_level", models.DecimalField(blank=True, decimal_places=8, max_digits=24, null=True)),
                ("reason", models.TextField(blank=True)),
                ("confidence", models.FloatField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="signals", to="agent.agentrun")),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="AgentLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("level", models.CharField(choices=[("debug", "Debug"), ("info", "Info"), ("warning", "Warning"), ("error", "Error")], default="info", max_length=16)),
                ("message", models.TextField()),
                ("source", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="logs", to="agent.agentrun")),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
    ]
