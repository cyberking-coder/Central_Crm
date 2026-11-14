from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketing", "0002_seed_lead_sources"),
    ]

    operations = [
        migrations.AddField(
            model_name="campaign",
            name="currency",
            field=models.CharField(
                blank=True, help_text="ISO-3; blank = company default.",
                max_length=3),
        ),
        migrations.AddField(
            model_name="campaign",
            name="spend",
            field=models.DecimalField(
                decimal_places=2, default=0,
                help_text="Total ad spend recorded against this campaign.",
                max_digits=14),
        ),
    ]
