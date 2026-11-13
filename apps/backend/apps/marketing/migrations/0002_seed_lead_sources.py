from django.db import migrations


SOURCES = [
    ("Website", "website"),
    ("Facebook", "facebook"),
    ("Instagram", "instagram"),
    ("Google Ads", "google_ads"),
    ("Referral", "referral"),
    ("WhatsApp", "whatsapp"),
    ("Webinar", "webinar"),
    ("Manual", "manual"),
    ("Other", "other"),
]


def seed(apps, schema_editor):
    LeadSource = apps.get_model("marketing", "LeadSource")
    for name, slug in SOURCES:
        LeadSource.objects.get_or_create(slug=slug, defaults={"name": name})


def unseed(apps, schema_editor):
    apps.get_model("marketing", "LeadSource").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("marketing", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
