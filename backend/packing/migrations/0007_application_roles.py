from django.conf import settings
from django.db import migrations


def configure_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    User = apps.get_model(settings.AUTH_USER_MODEL)
    content_type, _ = ContentType.objects.get_or_create(app_label='packing', model='program')
    permissions = {}
    for code, name in [('consult', 'Consultar balances'), ('capture', 'Capturar empaque'), ('plan', 'Gestionar planeación'), ('release', 'Liberar empaque')]:
        permissions[code], _ = Permission.objects.get_or_create(content_type=content_type, codename=code, defaults={'name': name})
    for name, codes, legacy in [
        ('Planer', ['consult', 'capture', 'plan', 'release'], ['Planeación']),
        ('Operador', ['consult', 'capture', 'release'], ['Calidad']),
    ]:
        group, _ = Group.objects.get_or_create(name=name)
        group.permissions.set([permissions[code] for code in codes])
        for user in User.objects.filter(groups__name__in=legacy, is_superuser=False).distinct():
            user.groups.add(group)
            user.groups.remove(*Group.objects.filter(name__in=legacy))
    # Preserve consult-only accounts; normalize existing operational accounts.
    for user in User.objects.filter(is_superuser=False):
        direct = set(user.user_permissions.filter(content_type__app_label='packing').values_list('codename', flat=True))
        inherited = set(Permission.objects.filter(group__user=user, content_type__app_label='packing').values_list('codename', flat=True))
        codes = direct | inherited
        if 'plan' in codes:
            user.groups.add(Group.objects.get(name='Planer'))
        elif codes.intersection({'capture', 'release'}):
            user.groups.add(Group.objects.get(name='Operador'))


class Migration(migrations.Migration):
    dependencies = [
        ('packing', '0006_demand_archived'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [migrations.RunPython(configure_roles, migrations.RunPython.noop)]
