import os,sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'backend'));os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django;django.setup()
from packing.models import Part,Demand,IntegrationState
from django.db.models import Count
state=IntegrationState.objects.filter(name='universo').first()
issues=[]
for line in Demand.objects.select_related('part','program').annotate(captures_count=Count('capture')):
    part=line.part
    if part.customer.strip().casefold()!=line.program.client.strip().casefold() or not part.universe_id or part.provisional:
        issues.append({'id':line.pk,'folio':line.reference,'part':part.number,'order_customer':line.program.client,'universe_customer':part.customer,'published':line.program.published,'captures':line.captures_count,'universe_id':part.universe_id,'provisional':part.provisional})
report={'parts':Part.objects.count(),'confirmed_parts':Part.objects.filter(provisional=False,universe_id__isnull=False).count(),'last_sync':str(state.last_sync) if state else None,'issues':issues}
(root/'private'/'auditoria-clientes-piezas.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))

