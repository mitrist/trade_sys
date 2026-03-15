from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TickerDailyVolume",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(db_index=True)),
                ("symbol", models.CharField(db_index=True, max_length=32)),
                ("category", models.CharField(default="linear", max_length=16)),
                ("volume24h", models.DecimalField(blank=True, decimal_places=8, max_digits=24, null=True)),
                ("turnover24h", models.DecimalField(blank=True, decimal_places=8, max_digits=24, null=True)),
                ("high_price24h", models.DecimalField(blank=True, decimal_places=8, max_digits=24, null=True)),
                ("low_price24h", models.DecimalField(blank=True, decimal_places=8, max_digits=24, null=True)),
                ("last_price", models.DecimalField(blank=True, decimal_places=8, max_digits=24, null=True)),
            ],
            options={
                "ordering": ["-date", "symbol"],
            },
        ),
        migrations.CreateModel(
            name="SelectedTicker",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(db_index=True)),
                ("symbol", models.CharField(db_index=True, max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["date", "symbol"],
            },
        ),
        migrations.CreateModel(
            name="Candle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("symbol", models.CharField(db_index=True, max_length=32)),
                ("interval", models.CharField(db_index=True, max_length=8)),
                ("start_time", models.DateTimeField(db_index=True)),
                ("open", models.DecimalField(decimal_places=8, max_digits=24)),
                ("high", models.DecimalField(decimal_places=8, max_digits=24)),
                ("low", models.DecimalField(decimal_places=8, max_digits=24)),
                ("close", models.DecimalField(decimal_places=8, max_digits=24)),
                ("volume", models.DecimalField(decimal_places=8, max_digits=24)),
                ("turnover", models.DecimalField(blank=True, decimal_places=8, max_digits=24, null=True)),
            ],
            options={
                "ordering": ["symbol", "interval", "start_time"],
            },
        ),
        migrations.AddConstraint(
            model_name="tickerdailyvolume",
            constraint=models.UniqueConstraint(fields=("date", "symbol", "category"), name="unique_ticker_daily_volume"),
        ),
        migrations.AddConstraint(
            model_name="selectedticker",
            constraint=models.UniqueConstraint(fields=("date", "symbol"), name="unique_selected_ticker"),
        ),
        migrations.AddConstraint(
            model_name="candle",
            constraint=models.UniqueConstraint(fields=("symbol", "interval", "start_time"), name="unique_candle"),
        ),
    ]
