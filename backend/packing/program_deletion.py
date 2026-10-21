"""Review and delete programs that have no operational history."""
import hashlib
import json
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import Program, Capture, OpeningBalance, Allocation, Revision, ClosedPeriod
from .services import require, lock_ledger, audit, check_open


def review(program):
    orders=list(program.lines.order_by('id').values('id','reference','part__number','quantity'))
    info={'id':program.pk,'client':program.client,'scope':program.scope,'year':program.year,'week':program.week,'reference':program.reference,'published':program.published,'version':program.version}
    reasons=[]
    if Capture.objects.filter(target__program=program).exists():
        reasons.append('El programa tiene capturas registradas, incluidas las anuladas. Conserva su historial; puedes ocultarlo de piso.')
    if OpeningBalance.objects.filter(demand__program=program).exists():
        reasons.append('El programa tiene saldos iniciales registrados.')
    if Allocation.objects.filter(demand__program=program).exists():
        reasons.append('El programa tiene asignaciones de producción o excedentes.')
    if Revision.objects.filter(demand__program=program).exists():
        reasons.append('El programa tiene revisiones de demanda registradas.')
    if ClosedPeriod.objects.filter(date=timezone.localdate()).exists():
        reasons.append('La fecha operativa actual está cerrada.')
    signature=hashlib.sha256(json.dumps({'program':info,'orders':orders},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return {'program':info,'orders':orders,'order_count':len(orders),'quantity':sum(row['quantity'] for row in orders),'can_delete':not reasons,'blocked_reasons':reasons,'confirmation':signature}


@transaction.atomic
def inspect(actor,pk):
    require(actor,'plan');lock_ledger()
    return review(Program.objects.select_for_update().get(pk=pk))


@transaction.atomic
def delete(actor,pk,reason,confirmation):
    require(actor,'plan');lock_ledger();check_open(timezone.localdate())
    program=Program.objects.select_for_update().get(pk=pk)
    current=review(program)
    if not current['can_delete']:raise ValidationError(' '.join(current['blocked_reasons']))
    if not confirmation or confirmation!=current['confirmation']:
        raise ValidationError('El programa cambió o no se ha revisado. Vuelve a abrir la confirmación antes de eliminarlo.')
    if not isinstance(reason,str) or not reason.strip():raise ValidationError('Indica el motivo de eliminación.')
    audit(actor,'delete_program',program,reason.strip(),program=current['program'],orders=current['orders'])
    try:
        program.lines.all().delete()
        program.delete()
    except ProtectedError as exc:
        raise ValidationError('El programa tiene registros relacionados y no puede eliminarse.') from exc
    return {'deleted':True,'id':pk,'orders_deleted':current['order_count']}
