"""Explicitly apply available surplus to compatible orders in the next ISO week."""
import uuid
from datetime import date, timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import Demand, Capture, OpeningBalance, WeekTransfer
from . import services as s


@transaction.atomic
def move(actor, pk, payload):
    s.require(actor, 'plan')
    s.lock_ledger()
    s.check_open(timezone.localdate())
    try:
        key = uuid.UUID(str(payload['key']))
        start = date.fromisocalendar(int(payload['year']), int(payload['week']), 1)
    except (ValueError, TypeError, KeyError, OverflowError):
        raise ValidationError('Indica la semana de origen y un identificador de envío válidos.')
    previous = WeekTransfer.objects.filter(key=key).first()
    if previous:
        if previous.demand_id != pk or previous.actor_id != actor.pk or previous.from_start != start or previous.result.get('kind') != 'surplus':
            raise ValidationError('El identificador ya se utilizó en otra operación.')
        return previous.result
    origin = Demand.objects.select_for_update().select_related('program', 'part').get(pk=pk)
    if origin.archived or not origin.program.published:
        raise ValidationError('La orden de origen debe estar publicada y disponible.')
    s.validate_part_customer(origin.part, origin.program.client)
    if start != origin.program.starts_on:
        raise ValidationError('La semana de origen cambió. Actualiza las órdenes.')
    sources = [*Capture.objects.filter(target=origin, released=True, voided=False).order_by('created_at', 'pk'),
               *OpeningBalance.objects.filter(demand=origin).order_by('created_at', 'pk')]
    sources = [source for source in sources if s.available(source) > 0]
    credit = sum(s.available(source) for source in sources)
    if not credit:
        raise ValidationError('Esta orden no tiene excedente liberado disponible. Sus pendientes no se trasladarán.')
    if payload.get('expected_credit') is not None and s.positive(payload['expected_credit']) != credit:
        raise ValidationError('El excedente disponible cambió. Actualiza las órdenes y revisa la cantidad antes de confirmar.')
    destination = start + timedelta(days=7)
    targets = [line for line in Demand.objects.select_for_update().filter(
        part=origin.part, program__scope=origin.program.scope, program__starts_on=destination,
        program__published=True, archived=False).select_related('program', 'part').order_by('pk')
        if s.compatible(origin, line)]
    if not targets:
        raise ValidationError('No hay una orden compatible publicada en la siguiente semana. El saldo permanece en Excedentes.')
    movements = []
    for source in sources:
        opening = isinstance(source, OpeningBalance)
        source_day = timezone.localtime(source.cutoff).date() if opening else source.operational_date
        s.check_open(source_day)
        for target in targets:
            amount = min(s.available(source), s.packing_pending(target))
            if amount:
                s.allocate(source, target, amount)
                movements.append({'source':source.pk, 'opening':opening, 'demand':target.pk, 'quantity':amount})
    applied = sum(item['quantity'] for item in movements)
    if not applied:
        raise ValidationError('Las órdenes de la siguiente semana ya están cubiertas o tienen empaque reservado. El excedente permanece disponible.')
    year, week, _ = destination.isocalendar()
    result = {'kind':'surplus', 'from_year':start.isocalendar().year, 'from_week':start.isocalendar().week,
              'year':year, 'week':week, 'credit':credit, 'applied_credit':applied,
              'remaining_credit':credit-applied, 'pending':0, 'movements':movements}
    WeekTransfer.objects.create(key=key, demand=origin, actor=actor, from_start=start, to_start=destination, result=result)
    s.audit(actor, 'next_week_surplus', origin, 'Excedente aplicado a la siguiente semana', result=result)
    return result
