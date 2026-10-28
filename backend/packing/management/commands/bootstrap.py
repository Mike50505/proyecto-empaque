from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from packing.models import BalanceGroup, Shift
class Command(BaseCommand):
    help='Crea grupos y permisos. No crea usuarios ni contraseñas.'
    def handle(self,*args,**kwargs):
        for name in ['Lennox','Daikin','Monterrey','Rheem']: BalanceGroup.objects.get_or_create(name=name)
        for code in ['A','B','No determinado/combinado']: Shift.objects.get_or_create(code=code)
        for name,roles in {'Planer':['consult','capture','plan','release'],'Operador':['consult','capture','release']}.items():
            group,_=Group.objects.get_or_create(name=name)
            group.permissions.set(Permission.objects.filter(content_type__app_label='packing',codename__in=roles))
        self.stdout.write('Catálogos y roles inicializados. Horarios A/B pendientes de validación.')
