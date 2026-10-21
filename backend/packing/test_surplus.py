import uuid
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient
from .models import BalanceGroup, Part, Program, Demand, Capture, Allocation, OpeningBalance, Employee, Shift, ClosedPeriod
from . import services as s
from .surplus import apply_all


class SurplusAcceptance(TransactionTestCase):
    def setUp(self):
        self.actor=get_user_model().objects.create_superuser(username='surplus-test', password=None)
        self.group=BalanceGroup.objects.create(name='SINTÉTICO SOBRANTES')
        self.part=Part.objects.create(number='613366-01', customer='LENNOX 1', universe_id=str(uuid.uuid4()), provisional=False)
        self.shift=Shift.objects.create(code='A')
        self.employee=Employee.objects.create(payroll='TEST', name='Sintético', inspector=True)

    def line(self, quantity, week, scope='DESTINO', published=True, part=None):
        program=Program.objects.create(group=self.group, client='LENNOX 1', scope=scope, year=2026, week=week, starts_on=date.fromisocalendar(2026, week, 1), ends_on=date.fromisocalendar(2026, week, 7), reference=str(uuid.uuid4()), published=published)
        return Demand.objects.create(program=program, part=part or self.part, reference=str(uuid.uuid4()), original=quantity, quantity=quantity)

    def pack(self, line, quantity, released=True, day=None):
        event=Capture.objects.create(target=line, quantity=quantity, fingerprint='test', effective_at=timezone.now(), operational_date=day or timezone.localdate(), shift=self.shift, packer=self.employee, inspector=self.employee if released else None, actor=self.actor, released=released, release_mode='declared')
        if released:
            s.allocate(event, line)
        return event

    def test_29_surplus_applies_once_without_new_physical_capture(self):
        origin=self.line(250, 43)
        source=self.pack(origin, 279)
        target=self.line(600, 44)
        client=APIClient();client.force_authenticate(self.actor)
        response=client.post('/api/surplus/apply/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['quantity'], 29)
        self.assertEqual(response.data['orders'], 1)
        self.assertEqual(s.applied(target), 29)
        self.assertEqual(s.packing_pending(target), 571)
        self.assertEqual(s.available(source), 0)
        target.refresh_from_db()
        self.assertEqual(target.quantity, 600)
        self.assertEqual(Capture.objects.count(), 1)
        count=Allocation.objects.count()
        self.assertEqual(apply_all(self.actor)['quantity'], 0)
        self.assertEqual(Allocation.objects.count(), count)
        row=next(row for row in s.balance(self.actor, {})['rows'] if row['id']==target.pk)
        self.assertEqual((row['packed'], row['pending'], row['packing_pending']), (0,571,571))

    def test_splits_across_subsequent_orders_oldest_first_and_keeps_remainder(self):
        origin=self.line(100, 43);source=self.pack(origin, 200)
        self.line(99, 42)  # Older demand is not a subsequent order.
        latest=self.line(40, 45)
        first=self.line(30, 44)
        result=apply_all(self.actor)
        self.assertEqual(result['quantity'], 70)
        self.assertEqual([m['demand'] for m in result['movements']], [first.pk, latest.pk])
        self.assertEqual(s.available(source), 30)
        extra=self.line(20, 46)
        self.assertEqual(apply_all(self.actor)['quantity'], 20)
        self.assertEqual(s.applied(extra), 20)
        self.assertEqual(s.available(source), 10)

    def test_excludes_drafts_other_identity_destination_and_unreleased_sources(self):
        origin=self.line(100,43);self.pack(origin,129)
        other=Part.objects.create(number='613366-01', customer='LENNOX 1', universe_id=str(uuid.uuid4()), provisional=False)
        blocked=[self.line(50,44,scope='OTRO'), self.line(50,44,published=False), self.line(50,44,part=other)]
        self.assertEqual(apply_all(self.actor)['quantity'],0)
        self.assertTrue(all(s.applied(line)==0 for line in blocked))
        other_origin=self.line(100,43,scope='SIN LIBERAR')
        self.pack(other_origin,129,released=False)
        target=self.line(50,44,scope='SIN LIBERAR')
        self.assertEqual(apply_all(self.actor)['quantity'],0)
        self.assertEqual(s.applied(target),0)

    def test_does_not_consume_capacity_already_packed_awaiting_release(self):
        origin=self.line(100,43);source=self.pack(origin,129)
        target=self.line(100,44);self.pack(target,90,released=False)
        self.assertEqual(apply_all(self.actor)['quantity'],10)
        self.assertEqual(s.available(source),19)
        self.assertEqual(s.packing_pending(target),0)
        self.assertEqual(apply_all(self.actor)['quantity'],0)

    def test_opening_credit_and_closed_sources(self):
        origin=self.line(100,43)
        opening=OpeningBalance.objects.create(demand=origin,applied=100,credit=29,cutoff=timezone.now())
        s.allocate(opening,origin)
        target=self.line(100,44)
        self.assertEqual(apply_all(self.actor)['quantity'],29)
        self.assertEqual(s.applied(target),29)
        yesterday=timezone.localdate()-timedelta(days=1)
        self.pack(origin,10,day=yesterday)
        ClosedPeriod.objects.create(date=yesterday,reason='Cierre sintético',actor=self.actor)
        result=apply_all(self.actor)
        self.assertEqual(result['quantity'],0)
        self.assertEqual(result['skipped_closed'],1)

    def test_requires_planning_permission(self):
        user=get_user_model().objects.create_user(username='read-only')
        with self.assertRaises(PermissionDenied):apply_all(user)
