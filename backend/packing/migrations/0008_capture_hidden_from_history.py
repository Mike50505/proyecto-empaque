from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('packing', '0007_application_roles'),
    ]

    operations = [
        migrations.AddField(
            model_name='capture',
            name='hidden_from_history',
            field=models.BooleanField(default=False),
        ),
    ]
