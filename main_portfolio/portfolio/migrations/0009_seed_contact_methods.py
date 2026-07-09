from django.db import migrations

def seed_contact_methods(apps, schema_editor):
    ContactMethod = apps.get_model('portfolio', 'ContactMethod')
    # Add default Email
    ContactMethod.objects.get_or_create(
        name="Email",
        value="sahilrajput5321@gmail.com",
        link="mailto:sahilrajput5321@gmail.com",
        icon_class="fa-solid fa-envelope",
        order=1
    )
    # Add default Phone
    ContactMethod.objects.get_or_create(
        name="Phone",
        value="+91 7404304607",
        link="tel:+917404304607",
        icon_class="fa-solid fa-phone",
        order=2
    )

def remove_contact_methods(apps, schema_editor):
    ContactMethod = apps.get_model('portfolio', 'ContactMethod')
    ContactMethod.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0008_contactmethod'),
    ]

    operations = [
        migrations.RunPython(seed_contact_methods, remove_contact_methods),
    ]
