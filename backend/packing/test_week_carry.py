import uuid
from datetime import date, datetime, time, timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from .models import BalanceGroup, Part, Program, Demand, Shift, WeekTransfer, ClosedPeriod, Capture, OpeningBalance, Allocation
from . import services as s
from .surplus import inventory


class SurplusNextWeekTests(TestCase):
    def setUp(self):
        self.actor=get_user_model().objects.create_superuser('week-test',password=None)
        self.group=BalanceGroup.objects.create(name='SYNTHETIC')
        self.part=Part.objects.create(number='WEEK-01',customer='LENNOX 1',universe_id=str(uuid.uuid4()),provisional=False)
        Shift.objects.create(code='A')
        self.client=APIClient();self.client.force_authenticate(self.actor)

    def line(self,qty,week=43,year=2026,scope='SLP',client=None):
        program=Program.objects.create(group=self.group,client=client or self.part.customer,scope=scope,year=year,week=week,starts_on=date.fromisocalendar(year,week,1),ends_on=date.fromisocalendar(year,week,7),reference=str(uuid.uuid4()),published=True)
        return Demand.objects.create(program=program,part=self.part,reference=str(uuid.uuid4()),original=qty,quantity=qty)

    def pack(self,line,qty):
        day=timezone.localdate()-timedelta(days=1)
        return s.capture(self.actor,{'key':str(uuid.uuid4()),'demand':line.pk,'quantity':qty,'effective_at':timezone.make_aware(datetime.combine(day,time(10))).isoformat(),'operational_date':str(day),'packer':'00007','inspector':'00045','accept_excess':True})

    def move(self,line,week=43,year=2026,key=None):
        return self.client.post(f'/api/demands/{line.pk}/next-week/',{'key':str(key or uuid.uuid4()),'year':year,'week':week},format='json')

    def test_only_surplus_applies_without_moving_demands_or_adding_production(self):
        origin=self.line(100);target=self.line(200,44);self.pack(origin,130)
        result=self.move(origin)
        self.assertEqual(result.status_code,200,result.data)
        self.assertEqual(result.data['applied_credit'],30)
        self.assertEqual(s.applied(origin),100);self.assertEqual(s.applied(target),30)
        self.assertEqual(s.balance(self.actor,{'year':'2026','week':'44'})['totals']['pending'],170)
        origin.refresh_from_db();self.assertIsNone(origin.carry_to)
        self.assertEqual(origin.program.week,43);self.assertEqual(Capture.objects.count(),1)

    def test_pending_without_surplus_is_not_moved(self):
        origin=self.line(100);target=self.line(200,44);self.pack(origin,40)
        self.assertEqual(self.move(origin).status_code,400)
        self.assertEqual(s.applied(target),0)
        self.assertEqual(s.balance(self.actor,{'year':'2026','week':'43'})['totals']['pending'],60)
        origin.refresh_from_db();self.assertIsNone(origin.carry_to)

    def test_remainder_stays_in_inventory(self):
        origin=self.line(100);target=self.line(20,44);source=self.pack(origin,150)
        result=self.move(origin)
        self.assertEqual(result.status_code,200,result.data)
        self.assertEqual((result.data['applied_credit'],result.data['remaining_credit']),(20,30))
        self.assertEqual(s.available(source),30);self.assertEqual(inventory(self.actor,{})['total'],30)

    def test_next_week_only_and_matching_destination(self):
        origin=self.line(100);self.pack(origin,130)
        wrong_destination=self.line(100,44,scope='OTHER');later=self.line(100,45)
        self.assertEqual(self.move(origin).status_code,400)
        self.assertEqual(s.applied(wrong_destination),0);self.assertEqual(s.applied(later),0)
        self.assertEqual(inventory(self.actor,{})['total'],30)

    def test_idempotent_retry_and_stale_week(self):
        origin=self.line(100);target=self.line(200,44);self.pack(origin,130);key=uuid.uuid4()
        first=self.move(origin,key=key);second=self.move(origin,key=key)
        self.assertEqual(first.status_code,200);self.assertEqual(first.data,second.data)
        self.assertEqual(WeekTransfer.objects.count(),1);self.assertEqual(s.applied(target),30)
        self.assertEqual(self.move(origin,44).status_code,400)

    def test_planer_can_apply_operator_cannot(self):
        origin=self.line(100);self.line(100,44);self.pack(origin,130)
        for role,status in [('Operador',403),('Planer',200)]:
            user=get_user_model().objects.create_user(role);user.groups.add(Group.objects.get(name=role));self.client.force_authenticate(user)
            self.assertEqual(self.move(origin).status_code,status)

    def test_year_rollover(self):
        origin=self.line(100,53);self.line(100,1,2027);self.pack(origin,130)
        result=self.move(origin,53)
        self.assertEqual(result.status_code,200,result.data)
        self.assertEqual((result.data['year'],result.data['week']),(2027,1))

    def test_closed_source_rejects_without_partial_allocations(self):
        origin=self.line(100);target=self.line(200,44);source=self.pack(origin,130)
        ClosedPeriod.objects.create(date=source.operational_date,reason='Test',actor=self.actor)
        self.assertEqual(self.move(origin).status_code,400)
        self.assertEqual(s.applied(target),0);self.assertEqual(s.available(source),30)

    def test_pending_physical_capture_is_reserved(self):
        origin=self.line(100);target=self.line(100,44);self.pack(origin,150)
        waiting=self.pack(target,90)
        waiting.allocations.all().delete();waiting.released=False;waiting.save()
        result=self.move(origin)
        self.assertEqual(result.status_code,200,result.data)
        self.assertEqual(result.data['applied_credit'],10)
        self.assertEqual(result.data['remaining_credit'],40)

    def test_opening_surplus_is_applied_with_existing_allocations_preserved(self):
        origin=self.line(100);target=self.line(100,44)
        source=OpeningBalance.objects.create(demand=origin,applied=100,credit=25,cutoff=timezone.now())
        Allocation.objects.create(opening=source,demand=origin,quantity=100)
        result=self.move(origin)
        self.assertEqual(result.status_code,200,result.data)
        self.assertEqual(s.applied(origin),100);self.assertEqual(s.applied(target),25)

    def test_stale_review_amount_does_not_move_a_different_quantity(self):
        origin=self.line(100);target=self.line(100,44);self.pack(origin,130)
        result=self.client.post(f'/api/demands/{origin.pk}/next-week/',{'key':str(uuid.uuid4()),'year':2026,'week':43,'expected_credit':20},format='json')
        self.assertEqual(result.status_code,400)
        self.assertEqual(s.applied(target),0)
        self.assertEqual(inventory(self.actor,{})['total'],30)
