import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('packing', '0008_capture_hidden_from_history'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ExtraCapture',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('fingerprint', models.CharField(max_length=64)),
                ('part_number', models.CharField(max_length=120)),
                ('quantity', models.PositiveIntegerField()),
                ('effective_at', models.DateTimeField()),
                ('operational_date', models.DateField()),
                ('packer_payroll', models.CharField(max_length=40)),
                ('inspector_payroll', models.CharField(max_length=40)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('hidden_from_history', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True)),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('shift', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='packing.shift')),
            ],
        ),
        migrations.AddConstraint(
            model_name='extracapture',
            constraint=models.CheckConstraint(condition=models.Q(('quantity__gt', 0)), name='positive_extra_capture'),
        ),
        migrations.AddIndex(
            model_name='extracapture',
            index=models.Index(fields=['operational_date', 'shift'], name='packing_ext_operat_0773b2_idx'),
        ),
    ]
