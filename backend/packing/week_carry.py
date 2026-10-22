"""Move the working week while retaining original commitments and production."""
import uuid
from datetime import date, timedelta
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import Demand, Capture, OpeningBalance, Allocation, WeekTransfer, ClosedPeriod
from .client_groups import client_group
from . import services as s


def credit(line):
    return sum(s.available(event) for event in Capture.objects.filter(target=line,released=True,voided=False)) + sum(s.available(opening) for opening in OpeningBalance.objects.filter(demand=line))


def working_start(line):
    if not line.carry_to: return line.program.starts_on
    outstanding=max(line.quantity-s.applied(line),0)
    if line.carry_to and (outstanding or credit(line)>0 or Capture.objects.filter(target=line,voided=False,released=False).exists()):
        return line.carry_to
    return line.program.starts_on


def members(line, start=None):
    start=start or working_start(line)
    query=Demand.objects.filter(part_id=line.part_id,program__published=True,program__scope=line.program.scope,archived=False)
    if not query.filter(carry_to=start).exists(): return [line]
    candidates=list(query.filter(Q(program__starts_on=start)|Q(carry_to=start)).select_related('program','part').order_by('program__starts_on','pk'))
    matching=[item for item in candidates if s.compatible(line,item) and working_start(item)==start]
    if not any(item.carry_to==start for item in matching):
        return [line]
    return matching


def group_packing_pending(lines):
    physical=sum(s.total(Capture.objects.filter(target=line,voided=False))-s.total(Allocation.objects.filter(capture__target=line,active=True)) for line in lines)
    return max(sum(max(line.quantity-s.applied(line),0) for line in lines)-physical,0)


def release_capacity(lines):
    pending=sum(max(line.quantity-s.applied(line),0) for line in lines)
    reserved=s.total(Capture.objects.filter(target__in=lines,voided=False,released=False))
    return max(pending-reserved,0)


def allocate_work(source):
    line=source.target
    # A release belongs to the working week chosen before allocation. Completing
    # its original order must not change the remaining recipients mid-operation.
    lines=members(line,line.carry_to or line.program.starts_on)
    for target in lines:
        s.allocate(source,target)


def apply_credits(lines, actor):
    applied=0
    closed=set(ClosedPeriod.objects.values_list('date',flat=True))
    for origin in lines:
        sources=[(source,source.operational_date) for source in Capture.objects.filter(target=origin,released=True,voided=False).order_by('pk')]
        sources += [(source,timezone.localtime(source.cutoff).date()) for source in OpeningBalance.objects.filter(demand=origin).order_by('pk')]
        for source,day in sources:
            if not s.available(source): continue
            if not release_capacity(lines): continue
            if day in closed: raise ValidationError('El sobrante pertenece a un periodo cerrado. Planeación debe reabrirlo antes de trasladarlo.')
            for target in lines:
                amount=min(s.available(source),release_capacity([target]),release_capacity(lines))
                if amount>0:
                    s.allocate(source,target,amount)
                    applied+=amount
                    s.audit(actor,'transfer',source,'Sobrante aplicado al pasar a la siguiente semana',demand=target.pk,quantity=amount,opening=isinstance(source,OpeningBalance))
    return applied


def apply_waiting_credits(actor, programs):
    seen=set()
    targets=list(Demand.objects.filter(program__in=programs).select_related('program','part'))
    starts={program.starts_on for program in programs}
    for line in Demand.objects.filter(carry_to__in=starts,program__published=True,archived=False).select_related('program','part'):
        start=working_start(line)
        if not any(target.program.starts_on==start and s.compatible(line,target) for target in targets): continue
        key=(line.part_id,client_group(line.program.client),line.program.scope,start)
        if start!=line.carry_to or key in seen: continue
        seen.add(key)
        apply_credits(members(line,start),actor)


@transaction.atomic
def move(actor, pk, payload):
    s.require(actor,'plan');s.lock_ledger();s.check_open(timezone.localdate())
    try:
        key=uuid.UUID(str(payload['key']))
        start=date.fromisocalendar(int(payload['year']),int(payload['week']),1)
    except (ValueError,TypeError,KeyError,OverflowError):
        raise ValidationError('Indica la semana de trabajo y un identificador de envío válidos.')
    previous=WeekTransfer.objects.filter(key=key).first()
    if previous:
        if previous.demand_id!=pk or previous.actor_id!=actor.pk or previous.from_start!=start:
            raise ValidationError('El identificador ya se utilizó en otro traslado.')
        return previous.result
    line=Demand.objects.select_for_update().select_related('program','part').get(pk=pk)
    if line.archived: raise ValidationError('Este número ya fue retirado del programa.')
    if not line.program.published: raise ValidationError('Publica la orden antes de pasarla a otra semana.')
    s.validate_part_customer(line.part,line.program.client)
    if working_start(line)!=start: raise ValidationError('La semana de trabajo cambió. Actualiza las órdenes antes de continuar.')
    moving=members(line,start)
    if not any(max(item.quantity-s.applied(item),0)>0 or credit(item)>0 for item in moving):
        raise ValidationError('La pieza ya está cumplida y no tiene sobrantes disponibles.')
    destination=start+timedelta(days=7)
    pending=sum(max(item.quantity-s.applied(item),0) for item in moving)
    surplus=sum(credit(item) for item in moving)
    for item in moving:
        s.validate_part_customer(item.part,item.program.client)
        item.carry_to=destination;item.save(update_fields=['carry_to'])
    targets=members(line,destination)
    assigned=apply_credits(targets,actor)
    year,week,_=destination.isocalendar()
    result={'from_year':start.isocalendar().year,'from_week':start.isocalendar().week,'year':year,'week':week,'pending':pending,'credit':surplus,'applied_credit':assigned,'members':[item.pk for item in moving]}
    WeekTransfer.objects.create(key=key,demand=line,actor=actor,from_start=start,to_start=destination,result=result)
    s.audit(actor,'next_week',line,'Pasar a la siguiente semana',**result)
    return result


def project(rows, lines, params):
    by_id={line.pk:line for line in lines}
    groups={}
    history=[]
    for row in rows:
        line=by_id[row['id']]
        active=bool(line.carry_to and (row['pending'] or row['pending_release']))
        start=line.carry_to if active else line.program.starts_on
        year,week,_=start.isocalendar()
        if active:
            # Keep a completed-looking record in the commitment week while the
            # outstanding balance is shown in its current working week.
            archived=dict(row)
            archived.update(id=f"carry-history-{line.pk}",year=line.program.year,week=line.program.week,
                pending=0,packing_pending=0,pending_release=0,credit=0,packed=0,A=0,B=0,
                applied=line.quantity,carried=False,carry_history=True,
                carry_to_year=line.carry_to.isocalendar().year,carry_to_week=line.carry_to.isocalendar().week,
                origins=[],member_ids=[])
            history.append(archived)
        row.update(origin_year=line.program.year,origin_week=line.program.week,year=year,week=week,carried=active,part_id=line.part_id)
        row['origins']=[{'id':line.pk,'year':line.program.year,'week':line.program.week,'reference':line.reference,'pending':row['pending'],'credit':row['credit']}] if active else []
        groups.setdefault((line.part_id,row['client'],row['scope'],year,week,row['published']),[]).append(row)
    projected=[]
    sums=('original','quantity','applied','pending','credit','A','B','packed','pending_release','packing_pending')
    for group in groups.values():
        if not any(row['carried'] for row in group):
            projected.extend(group);continue
        row=dict(next(row for row in group if row['carried']))
        for key in sums: row[key]=sum(item[key] for item in group)
        # Group reservations need all unassigned physical units, including units
        # that exceed one member's pending but will satisfy another on release.
        ids=[item['id'] for item in group]
        unassigned=row['packed']-s.total(Allocation.objects.filter(capture__target_id__in=ids,active=True))
        row['packing_pending']=max(row['pending']-unassigned,0)
        row['origins']=[origin for item in group for origin in item['origins']]
        row['member_ids']=ids
        row['catalog_error']=' '.join(dict.fromkeys(item['catalog_error'] for item in group if item['catalog_error']))
        projected.append(row)
    projected.extend(history)
    selected=[]
    for row in projected:
        next_year,next_week,_=(date.fromisocalendar(row['year'],row['week'],1)+timedelta(days=7)).isocalendar()
        row.update(next_year=next_year,next_week=next_week)
        if params.get('year') and params.get('view')!='operational' and row['year']!=int(params['year']): continue
        if params.get('week'):
            if params.get('view')=='operational' and params.get('year'):
                if date.fromisocalendar(row['year'],row['week'],1)>date.fromisocalendar(int(params['year']),int(params['week']),1): continue
            elif row['week']!=int(params['week']): continue
        elif params.get('year') and row['year']!=int(params['year']): continue
        selected.append(row)
    return selected
