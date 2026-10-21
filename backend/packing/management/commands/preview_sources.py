from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from packing.importing import preview

class Command(BaseCommand):
    help='Prepara los cuatro libros reales SOLO en previsualización, sin demanda ni publicaciones.'
    def handle(self,*args,**kwargs):
        user=get_user_model().objects.filter(is_superuser=True).first()
        if not user:raise CommandError('Crear administrador antes de preparar previsualizaciones.')
        root=settings.BASE_DIR.parent
        sources=[('BALANCE LENNOX 1.xlsx','Lennox','SEMANA 43',43,'H','N'),('BALANCE DAIKIN SLP, EUA.xlsx','Daikin','SEMANA 42',42,'I','O'),('BALANCE MTY.xlsx','Monterrey','SEMANA 42 (2)',42,'I','O'),('BALANCE RHEEM TRANSFERENCIA, FALCON, CIP, NIPLES.xlsx','Rheem','SEMANA 34 OK',34,'I','O')]
        for filename,group,sheet,week,qty,bal in sources:
            path=root/filename
            if not path.exists():self.stdout.write('No disponible: '+filename);continue
            mapping={'sheet':sheet,'group':group,'year':2026,'week':week,'quantity_columns':[qty],'balance_column':bal,'reason':'Propuesta para revisión; confirmar año, semana, versión, columnas y equivalencias con Planeación. No oficializada.'}
            batch=preview(user,SimpleUploadedFile(filename,path.read_bytes()),'new',mapping)
            blocks=sum(i['severity']=='blocking' for i in batch.preview['issues'])
            self.stdout.write(f'{group}: lote #{batch.pk}; {len(batch.preview["rows"])} filas; {blocks} bloqueos; sin aplicar.')
