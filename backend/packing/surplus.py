"""Apply released surplus to subsequent published orders without new production."""
from collections import defaultdict
from django.db import transaction
from django.db.models import Q, Sum, F
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import Capture, OpeningBalance, Demand, ClosedPeriod
from .client_groups import client_group
from . import services as s


@transaction.atomic
def apply_all(actor):
    s.require(actor, 'plan')
    s.lock_ledger()
    s.check_open(timezone.localdate())
    closed=set(ClosedPeriod.objects.values_list('date', flat=True))
    lines=list(Demand.objects.filter(program__published=True).select_related('program', 'part').order_by('program__starts_on', 'id'))
    candidates=defaultdict(list)
    for line in lines:
        try:
            s.validate_part_customer(line.part, line.program.client)
        except ValidationError:
            continue
        candidates[(line.part_id, client_group(line.program.client), line.program.scope)].append(line)
    captures=Capture.objects.filter(released=True, voided=False, target__program__published=True).select_related('target__program', 'target__part').annotate(used=Coalesce(Sum('allocations__quantity', filter=Q(allocations__active=True)), 0)).filter(quantity__gt=F('used'))
    openings=OpeningBalance.objects.filter(demand__program__published=True).select_related('demand__program', 'demand__part').annotate(used=Coalesce(Sum('allocations__quantity', filter=Q(allocations__active=True)), 0)).filter(applied__gt=F('used')-F('credit'))
    sources=[(source.target, source, source.operational_date) for source in captures]
    sources += [(source.demand, source, timezone.localtime(source.cutoff).date()) for source in openings]
    sources.sort(key=lambda item:(item[0].program.starts_on, item[1].created_at, item[1].pk))
    pending={}
    movements=[]
    skipped_closed=0
    for origin, source, source_day in sources:
        if source_day in closed:
            skipped_closed+=1
            continue
        try:
            s.validate_part_customer(origin.part, origin.program.client)
        except ValidationError:
            continue
        # Only unassigned, released units are eligible. Never steal capacity
        # already occupied by physical work awaiting its own release.
        remaining=s.available(source)
        key=(origin.part_id, client_group(origin.program.client), origin.program.scope)
        for line in candidates[key]:
            if remaining<=0:
                break
            if (line.program.starts_on, line.pk)<=(origin.program.starts_on, origin.pk):
                continue
            if line.pk not in pending:
                pending[line.pk]=s.packing_pending(line)
            qty=min(remaining, pending[line.pk])
            if qty<=0:
                continue
            s.allocate(source, line, qty)
            pending[line.pk]-=qty
            remaining-=qty
            opening=isinstance(source, OpeningBalance)
            s.audit(actor, 'transfer', source, 'Aplicación masiva de sobrantes a órdenes siguientes', demand=line.pk, quantity=qty, opening=opening, bulk=True, origin=origin.pk)
            movements.append({'source':source.pk, 'opening':opening, 'origin':origin.pk, 'demand':line.pk, 'part':line.part.number, 'quantity':qty, 'from_week':origin.program.week, 'to_week':line.program.week})
    return {'quantity':sum(item['quantity'] for item in movements), 'orders':len({item['demand'] for item in movements}), 'skipped_closed':skipped_closed, 'movements':movements}
