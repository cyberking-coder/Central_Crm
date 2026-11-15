import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketing", "0003_campaign_currency_spend"),
    ]

    operations = [
        migrations.CreateModel(
            name="CampaignDailyMetrics",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("date", models.DateField(db_index=True)),
                ("spend", models.DecimalField(decimal_places=2, default=0,
                                               max_digits=14)),
                ("impressions", models.PositiveIntegerField(default=0)),
                ("clicks", models.PositiveIntegerField(default=0)),
                ("conversions", models.PositiveIntegerField(default=0)),
                ("currency", models.CharField(blank=True, max_length=3)),
                ("source", models.CharField(
                    blank=True,
                    help_text="e.g. 'meta_ads', 'google_ads'. Free-form.",
                    max_length=24)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("campaign", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="daily_metrics",
                    to="marketing.campaign")),
            ],
            options={"ordering": ["-date"]},
        ),
        migrations.AddConstraint(
            model_name="campaigndailymetrics",
            constraint=models.UniqueConstraint(
                fields=("campaign", "date"),
                name="campaign_daily_metrics_uniq"),
        ),
        migrations.AddIndex(
            model_name="campaigndailymetrics",
            index=models.Index(fields=["date", "campaign"],
                               name="camp_metrics_date_camp_idx"),
        ),
    ]
