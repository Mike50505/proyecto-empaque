import hashlib
import json
import uuid
from datetime import date, datetime, timedelta
from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied
from .models import *
from .part_validation import validate_part_customer
from .client_groups import client_group, client_filter

def require(user, role):
    if not user.is_authenticated or not (user.is_superuser or user.has_perm('packing.' + role)):
        raise PermissionDenied('No tienes permiso para esta operación.')

def audit(actor, kind, obj, reason='', **data):
    Audit.objects.create(actor=actor, kind=kind, object_id=str(obj.pk), reason=reason, data=data)

def positive(value, allow_zero=False):
    if isinstance(value, bool) or str(value).strip() != str(int(value)) or int(value) < (0 if allow_zero else 1):
        raise ValidationError('La cantidad debe ser un entero ' + ('no negativo.' if allow_zero else 'positivo.'))
    return int(value)

def total(qs): return qs.aggregate(n=Sum('quantity'))['n'] or 0
def applied(line): return total(line.allocations.filter(active=True))
def packing_pending(line):
    physical=total(Capture.objects.filter(target=line,voided=False))
    assigned=total(Allocation.objects.filter(capture__target=line,active=True))
    return max(line.quantity-applied(line)-(physical-assigned),0)
def available(source):
    if isinstance(source, Capture):
        return 0 if source.voided or not source.released else source.quantity - total(source.allocations.filter(active=True))
    return source.applied + source.credit - total(source.allocations.filter(active=True))

def check_open(day):
    if ClosedPeriod.objects.filter(date=day).exists():
        raise ValidationError('El periodo está cerrado; Planeación debe reabrirlo con motivo.')

def lock_ledger():
    # Orden global único: evita carreras de saldos, cortes y cierres. Optimizable por ámbito.
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute('SELECT pg_advisory_xact_lock(734290011)')

def compatible(a, b):
    return a.part_id == b.part_id and client_group(a.program.client) == client_group(b.program.client) and a.program.scope == b.program.scope

def allocate(source, line, amount=None):
    origin = source.target if isinstance(source, Capture) else source.demand
    validate_part_customer(origin.part,origin.program.client)
    validate_part_customer(line.part,line.program.client)
    if not line.program.published or not compatible(origin, line):
        raise ValidationError('Programa no publicado o pieza/cliente/destino incompatibles.')
    qty = min(available(source), max(line.quantity - applied(line), 0))
    if amount is not None:
        amount = positive(amount)
        if amount > qty: raise ValidationError('Cantidad superior al crédito o pendiente disponible.')
        qty = amount
    if qty:
        Allocation.objects.create(demand=line, quantity=qty, **({'capture':source} if isinstance(source, Capture) else {'opening':source}))
    return qty

def parse_time(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00')) if isinstance(value, str) else value
    if not result or timezone.is_naive(result): raise ValidationError('La fecha efectiva debe incluir zona horaria.')
    return result

@transaction.atomic
def capture(actor, payload):
    require(actor, 'capture')
    lock_ledger()
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    try: key = uuid.UUID(str(payload['key']))
    except (ValueError, KeyError): raise ValidationError('Identificador de envío inválido.')
    existing = Capture.objects.filter(key=key).first()
    if existing:
        if existing.fingerprint != fingerprint or existing.actor_id != actor.id: raise ValidationError('Conflicto: el identificador ya se utilizó con otro contenido.')
        return existing
    line = Demand.objects.select_for_update().select_related('program').get(pk=payload['demand'])
    if line.archived: raise ValidationError('Este número ya fue retirado del programa.')
    if not line.program.published: raise ValidationError('El programa todavía no está publicado.')
    validate_part_customer(line.part,line.program.client)
    qty = positive(payload['quantity'])
    from .week_carry import members, group_packing_pending, allocate_work
    if qty > group_packing_pending(members(line)) and not payload.get('accept_excess'):
        raise ValidationError('La cantidad genera excedente; revisa y confirma el excedente previsto.')
    effective = parse_time(payload['effective_at'])
    local_effective=timezone.localtime(effective)
    local_time=local_effective.time()
    minute=local_time.hour*60+local_time.minute
    if 4*60+38<=minute<16*60+37: shift_code='A'
    else: shift_code='B'
    day=date.fromisoformat(payload['operational_date'])
    if shift_code=='B' and minute<=4*60+37: day=local_effective.date()-timedelta(days=1)
    check_open(day)
    opening=OpeningBalance.objects.filter(demand=line).order_by('-cutoff').first()
    if opening and effective<=opening.cutoff:
        raise ValidationError('La captura es anterior al corte inicial y puede estar incluida en el saldo legado; requiere conciliación autorizada.')
    if effective > timezone.now(): raise ValidationError('La fecha de trabajo no puede estar en el futuro.')
    if abs((timezone.localtime(effective).date()-day).days)>1: raise ValidationError('La fecha operativa debe corresponder a la jornada efectiva.')
    payroll=str(payload.get('packer','')).strip()
    if not payroll: raise ValidationError('La nómina del empacador es obligatoria.')
    inspector = None
    released = False
    event = Capture.objects.create(key=key, fingerprint=fingerprint, target=line, quantity=qty, effective_at=effective, operational_date=day, shift=Shift.objects.get(code=shift_code), packer_payroll=payroll, inspector=inspector, actor=actor, released=released, release_mode=settings.RELEASE_MODE, notes=payload.get('notes',''))
    if released: allocate_work(event)
    audit(actor,'capture',event,quantity=qty)
    return event

@transaction.atomic
def release(actor, pk, inspector_payroll):
    require(actor,'release'); lock_ledger()
    event = Capture.objects.select_for_update().get(pk=pk)
    check_open(event.operational_date)
    if event.voided: raise ValidationError('Captura anulada.')
    payroll=str(inspector_payroll or '').strip()
    if not payroll: raise ValidationError('La nómina del inspector es obligatoria.')
    if not event.released:
        event.inspector = None; event.inspector_payroll = payroll
        event.released = True; event.released_by = actor; event.save()
        if not event.target.archived:
            from .week_carry import allocate_work
            allocate_work(event)
        audit(actor,'release',event)
    return event

@transaction.atomic
def transfer(actor, source_id, demand_id, quantity, reason, opening=False):
    require(actor,'plan'); lock_ledger()
    if not reason.strip(): raise ValidationError('Indica el motivo de la asignación.')
    source = (OpeningBalance if opening else Capture).objects.select_for_update().get(pk=source_id)
    check_open(timezone.localdate())
    if isinstance(source,Capture): check_open(source.operational_date)
    line = Demand.objects.select_for_update().get(pk=demand_id)
    n = allocate(source,line,quantity)
    audit(actor,'transfer',source,reason,demand=line.pk,quantity=n,opening=opening)
    return n

@transaction.atomic
def revise(actor, pk, quantity, reason):
    require(actor,'plan'); lock_ledger(); check_open(timezone.localdate())
    if not reason.strip(): raise ValidationError('Indica el motivo de la revisión.')
    line = Demand.objects.select_for_update().get(pk=pk)
    n = positive(quantity,True); before = line.quantity
    remove = max(applied(line)-n,0)
    for a in line.allocations.filter(active=True).order_by('-created_at','-id'):
        if remove <= 0: break
        if a.capture_id: check_open(a.capture.operational_date)
        reduction = min(remove,a.quantity)
        a.active=False; a.save(update_fields=['active'])
        if a.quantity>reduction: Allocation.objects.create(capture=a.capture,opening=a.opening,demand=line,quantity=a.quantity-reduction)
        remove-=reduction
    line.quantity=n; line.save(update_fields=['quantity'])
    Revision.objects.create(demand=line,before=before,after=n,reason=reason,actor=actor)
    line.program.version+=1; line.program.save(update_fields=['version'])
    audit(actor,'revision',line,reason,before=before,after=n)
    return line

@transaction.atomic
def correct(actor, pk, quantity, reason, replacement_key):
    require(actor,'plan'); lock_ledger()
    if not reason.strip(): raise ValidationError('Indica el motivo de la corrección.')
    event = Capture.objects.select_for_update().get(pk=pk)
    check_open(event.operational_date)
    if event.voided: raise ValidationError('La captura ya fue anulada.')
    quantity = positive(quantity,True)
    old_allocations = list(event.allocations.filter(active=True).order_by('created_at','id'))
    for a in old_allocations:
        if ClosedPeriod.objects.filter(date__gte=event.operational_date).exists():
            raise ValidationError('Hay periodos cerrados afectados; reabre antes de corregir.')
    event.allocations.filter(active=True).update(active=False)
    event.voided=True; event.save(update_fields=['voided'])
    replacement=None
    if quantity:
        replacement=Capture.objects.create(key=replacement_key,fingerprint=hashlib.sha256(str(replacement_key).encode()).hexdigest(),target=event.target,quantity=quantity,effective_at=event.effective_at,operational_date=event.operational_date,shift=event.shift,packer=event.packer,packer_payroll=event.packer_payroll,inspector=event.inspector,inspector_payroll=event.inspector_payroll,actor=actor,released=event.released,release_mode=event.release_mode,released_by=event.released_by,notes=reason)
        if replacement.released:
            for allocation in old_allocations:
                n=min(available(replacement),allocation.quantity,max(allocation.demand.quantity-applied(allocation.demand),0))
                if n: allocate(replacement,allocation.demand,n)
            allocate(replacement,event.target)
    audit(actor,'correction',event,reason,before=event.quantity,after=quantity,replacement=replacement.pk if replacement else None)
    CorrectionRequest.objects.filter(capture=event,resolved=False).update(resolved=True)
    return replacement

def demand_queryset(user, params, working=False, include_archived=False):
    require(user,'consult')
    qs=Demand.objects.select_related('program__group','part').order_by('priority','program__year','program__week','id')
    if not include_archived: qs=qs.filter(archived=False)
    if not (user.is_superuser or user.has_perm('packing.plan')): qs=qs.filter(program__published=True)
    if params.get('publication')=='published': qs=qs.filter(program__published=True)
    if params.get('publication')=='draft': qs=qs.filter(program__published=False)
    if params.get('priority')=='1': qs=qs.filter(priority=1)
    if params.get('group'): qs=qs.filter(program__group_id=params['group'])
    if params.get('client'): qs=qs.filter(client_filter('program__client',params['client']))
    if params.get('subclient'): qs=qs.filter(part__customer__iexact=params['subclient'])
    if params.get('scope'): qs=qs.filter(program__scope=params['scope'])
    if params.get('year') and not working: qs=qs.filter(program__year=params['year'])
    if params.get('week') and not working:
        if params.get('view')=='operational' and params.get('year'):
            qs=qs.filter(program__starts_on__lte=date.fromisocalendar(int(params['year']),int(params['week']),1))
        else: qs=qs.filter(program__week=params['week'])
    if params.get('search'): qs=qs.filter(Q(part__number__icontains=params['search']) | Q(part__diameter__icontains=params['search']))
    return qs

@transaction.atomic
def balance(user, params):
    lock_ledger()
    day=date.fromisoformat(params.get('date') or str(timezone.localdate()))
    lines=list(demand_queryset(user,params,working=True))
    ids=[line.pk for line in lines]
    applied_map={a['demand']:a['n'] for a in Allocation.objects.filter(demand_id__in=ids,active=True).values('demand').annotate(n=Sum('quantity'))}
    packed_map={a['target']:a['n'] for a in Capture.objects.filter(target_id__in=ids,voided=False).values('target').annotate(n=Sum('quantity'))}
    pending_release_map={a['target']:a['n'] for a in Capture.objects.filter(target_id__in=ids,voided=False,released=False).values('target').annotate(n=Sum('quantity'))}
    allocated_from_captures={a['capture__target']:a['n'] for a in Allocation.objects.filter(capture__target_id__in=ids,active=True).values('capture__target').annotate(n=Sum('quantity'))}
    shifts={}
    for item in Capture.objects.filter(target_id__in=ids,operational_date=day,voided=False).values('target','shift__code').annotate(n=Sum('quantity')):
        shifts.setdefault(item['target'],{})[item['shift__code']]=item['n']
    credits={}
    for item in Capture.objects.filter(target_id__in=ids,released=True,voided=False).annotate(used=Sum('allocations__quantity',filter=Q(allocations__active=True))):
        credits[item.target_id]=credits.get(item.target_id,0)+item.quantity-(item.used or 0)
    for item in OpeningBalance.objects.filter(demand_id__in=ids).annotate(used=Sum('allocations__quantity',filter=Q(allocations__active=True))):
        credits[item.demand_id]=credits.get(item.demand_id,0)+item.applied+item.credit-(item.used or 0)
    rows=[]
    for line in lines:
        catalog_error=''
        try: validate_part_customer(line.part,line.program.client)
        except ValidationError as exc: catalog_error=' '.join(str(item) for item in exc.detail)
        n=applied_map.get(line.pk,0)
        shift_totals=shifts.get(line.pk,{})
        credit=credits.get(line.pk,0)
        rows.append({'catalog_error':catalog_error,'id':line.pk,'program':line.program_id,'reference':line.reference,'group':line.program.group.name,'group_id':line.program.group_id,'client':client_group(line.program.client),'scope':line.program.scope,'year':line.program.year,'week':line.program.week,'part':line.attributes_snapshot.get('number',line.part.number),'diameter':line.attributes_snapshot.get('diameter',line.part.diameter),'original':line.original,'quantity':line.quantity,'applied':n,'pending':max(line.quantity-n,0),'credit':credit,'A':shift_totals.get('A',0),'B':shift_totals.get('B',0),'priority':line.priority,'published':line.program.published,'due_on':str(line.due_on) if line.due_on else None})
    quantity=sum(r['quantity'] for r in rows); done=sum(r['applied'] for r in rows)
    for row in rows:
        row['packed']=packed_map.get(row['id'],0)
        row['pending_release']=pending_release_map.get(row['id'],0)
        # El balance de piso descuenta capturas, incluso antes de Calidad, sin
        # duplicar créditos reasignados ni cantidades de saldos iniciales.
        unassigned_physical=row['packed']-allocated_from_captures.get(row['id'],0)
        row['packing_pending']=max(row['quantity']-row['applied']-unassigned_physical,0)
    from .week_carry import project
    rows=project(rows,lines,params)
    state=params.get('order_state','all')
    predicates={'pending':lambda r:r['pending']>0,'packing':lambda r:r['packing_pending']>0,'release':lambda r:r['pending_release']>0,'complete':lambda r:r['pending']==0,'credit':lambda r:r['credit']>0}
    if state in predicates: rows=[r for r in rows if predicates[state](r)]
    totals_rows=[r for r in rows if not r.get('carry_history')]
    quantity=sum(r['quantity'] for r in totals_rows); done=sum(r['applied'] for r in totals_rows)
    return {'rows':rows,'totals':{'quantity':quantity,'applied':done,'packed':sum(r['packed'] for r in totals_rows),'pending_release':sum(r['pending_release'] for r in totals_rows),'packing_pending':sum(r['packing_pending'] for r in totals_rows),'pending':sum(r['pending'] for r in totals_rows),'credit':sum(r['credit'] for r in totals_rows),'progress':round(100*done/quantity,2) if quantity else None},'date':str(day),'updated_at':timezone.now().isoformat()}

@transaction.atomic
def snapshot(actor, params, close=False, reason=''):
    require(actor,'plan'); lock_ledger()
    day=date.fromisoformat(params.get('date') or str(timezone.localdate()))
    if close and not reason.strip(): raise ValidationError('Indica el motivo del cierre.')
    payload=balance(actor,params)
    obj=Snapshot.objects.create(date=day,scope=params,version=Snapshot.objects.filter(date=day,scope=params).count()+1,payload=payload,cutoff=timezone.now(),actor=actor)
    if close: ClosedPeriod.objects.get_or_create(date=day,defaults={'reason':reason,'actor':actor})
    audit(actor,'snapshot',obj,reason,closed=close)
    return obj
