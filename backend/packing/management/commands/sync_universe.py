from django.core.management.base import BaseCommand
from packing.universe import sync
class Command(BaseCommand):
    help='Sincroniza el catálogo de Universo con caché local y cursor transaccional.'
    def add_arguments(self,parser): parser.add_argument('--full',action='store_true',help='Refresca todas las piezas desde la API oficial antes de aplicar cambios.')
    def handle(self,*args,**kwargs): self.stdout.write(str(sync(full=kwargs['full'])))
