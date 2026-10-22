import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('packing', '0002_alter_shift_code'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.AddField(model_name='demand', name='carry_to', field=models.DateField(blank=True, null=True)),
        migrations.CreateModel(name='WeekTransfer', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('key', models.UUIDField(unique=True)),
            ('from_start', models.DateField()),
            ('to_start', models.DateField()),
            ('result', models.JSONField(default=dict)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('actor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ('demand', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='week_transfers', to='packing.demand')),
        ]),
    ]
