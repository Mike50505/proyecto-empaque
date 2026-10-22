import uuid
from datetime import date,datetime,time as dt_time,timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError, PermissionDenied
from .models import BalanceGroup, Part, Program, Demand, Capture, Employee, Shift, WeekTransfer, ClosedPeriod
from . import services as s
from .week_carry import move


@override_settings(RELEASE_MODE='declared')
class WeekCarryTests(TestCase):
    def setUp(self):
        self.actor=get_user_model().objects.create_superuser(username='week-test',password=None)
        self.group=BalanceGroup.objects.create(name='TEST')
        self.part=Part.objects.create(number='WEEK-1',customer='LENNOX 1',universe_id=str(uuid.uuid4()),provisional=False)
        self.emp=Employee.objects.create(payroll='TEST',name='Test',inspector=True)
        Shift.objects.create(code='A')
        self.client=APIClient();self.client.force_authenticate(self.actor)

    def line(self,quantity,week=43,year=2026,scope='DESTINO',published=True):
        program=Program.objects.create(group=self.group,client=self.part.customer,scope=scope,year=year,week=week,starts_on=date.fromisocalendar(year,week,1),ends_on=date.fromisocalendar(year,week,7),reference=str(uuid.uuid4()),published=published)
        return Demand.objects.create(program=program,part=self.part,reference=str(uuid.uuid4()),original=quantity,quantity=quantity)

    def pack(self,line,qty,released=True):
        workday=timezone.localdate()-timedelta(days=1)
        effective=timezone.make_aware(datetime.combine(workday,dt_time(10)),timezone.get_current_timezone())
        event=s.capture(self.actor,{'key':str(uuid.uuid4()),'demand':line.pk,'quantity':qty,'effective_at':effective.isoformat(),'operational_date':str(timezone.localdate()),'shift':'A','packer':'TEST','inspector':'', 'accept_excess':True})
        return s.release(self.actor,event.pk,'TEST') if released else event

    def rows(self,week=None,year=2026):
        return s.balance(self.actor,{'week':str(week),'year':str(year)} if week else {})['rows']

    def move(self,line,week=43,year=2026,key=None):
        return move(self.actor,line.pk,{'key':str(key or uuid.uuid4()),'year':year,'week':week})

    def test_pending_merges_and_completion_returns_origin_without_duplicate_demand(self):
        origin=self.line(100);target=self.line(200,44)
        self.pack(origin,40)
        result=self.move(origin)
        self.assertEqual((result['pending'],result['week']),(60,44))
        origin_row=self.rows(43)[0]
        self.assertTrue(origin_row['carry_history'])
        self.assertEqual(origin_row['carry_to_week'],44)
        row=self.rows(44)[0]
        self.assertEqual((len(self.rows(44)),row['quantity'],row['pending']),(1,300,260))
        self.assertEqual(row['origins'][0]['week'],43)
        event=self.pack(origin,260)
        self.assertEqual(s.applied(origin),100);self.assertEqual(s.applied(target),200)
        self.assertEqual(s.available(event),0)
        self.assertEqual([row['id'] for row in self.rows(43)],[origin.pk])
        self.assertEqual([row['id'] for row in self.rows(44)],[target.pk])
        self.assertEqual(Demand.objects.count(),2)
        origin.refresh_from_db();self.assertEqual(origin.program.week,43);self.assertEqual(origin.quantity,100)

    def test_no_next_order_preserves_origin_until_completed(self):
        origin=self.line(100);self.pack(origin,30)
        self.move(origin)
        source=self.rows(43)[0]
        self.assertTrue(source['carry_history'])
        self.assertEqual(source['carry_to_week'],44)
        row=self.rows(44)[0]
        self.assertEqual((row['id'],row['pending'],row['origin_week']),(origin.pk,70,43))
        self.assertEqual(Demand.objects.count(),1)
        self.pack(origin,70)
        self.assertEqual(self.rows(44),[])
        self.assertEqual(self.rows(43)[0]['pending'],0)

    def test_surplus_subtracts_only_from_next_week_and_is_idempotent(self):
        origin=self.line(100);source=self.pack(origin,129)
        target=self.line(200,44);later=self.line(200,45)
        key=uuid.uuid4();result=self.move(origin,key=key)
        self.assertEqual((result['credit'],result['applied_credit']),(29,29))
        self.assertEqual(s.applied(target),29);self.assertEqual(s.applied(later),0)
        self.assertEqual(s.available(source),0)
        self.assertEqual(self.rows(44)[0]['pending'],171)
        self.assertEqual(self.move(origin,key=key),result)
        self.assertEqual(WeekTransfer.objects.count(),1)
        self.assertEqual(Capture.objects.count(),1)

    def test_surplus_without_target_waits_and_applies_when_target_is_published(self):
        origin=self.line(100);self.pack(origin,129);self.move(origin)
        row=self.rows(43)[0];self.assertEqual((row['credit'],row['pending'],row['week']),(29,0,43))
        target=self.line(200,44,published=False)
        response=self.client.post(f'/api/programs/{target.program_id}/publication/',{'published':True},format='json')
        self.assertEqual(response.status_code,200)
        self.assertEqual(s.applied(target),29)
        self.assertEqual([row['id'] for row in self.rows(43)],[origin.pk])
        self.assertEqual(self.rows(44)[0]['pending'],171)

    def test_unreleased_work_is_reserved_and_release_fulfills_oldest_first(self):
        origin=self.line(100);first=self.pack(origin,50,False)
        target=self.line(200,44);self.move(origin)
        row=self.rows(44)[0]
        self.assertEqual((row['pending_release'],row['packing_pending']),(50,250))
        event=self.pack(origin,250,False)
        self.assertEqual(self.rows(44)[0]['packing_pending'],0)
        s.release(self.actor,first.pk,'TEST');s.release(self.actor,event.pk,'TEST')
        self.assertEqual(s.applied(origin),100);self.assertEqual(s.applied(target),200)
        self.assertEqual(self.rows(43)[0]['pending'],0)

    def test_repeated_moves_and_iso_year_boundary(self):
        origin=self.line(100,53)
        self.move(origin,53)
        self.assertEqual(self.rows(1,2027)[0]['origin_week'],53)
        self.move(origin,1,2027)
        self.assertEqual(self.rows(2,2027)[0]['pending'],100)
        self.assertEqual(self.rows(1,2027),[])
        with self.assertRaises(ValidationError):self.move(origin,1,2027)

    def test_different_destination_and_draft_do_not_merge(self):
        origin=self.line(100);source=self.pack(origin,129)
        other=self.line(200,44,scope='OTRO');draft=self.line(200,44,published=False)
        self.move(origin)
        self.assertEqual(s.available(source),29)
        self.assertEqual(s.applied(other),0);self.assertEqual(s.applied(draft),0)
        self.assertEqual(len(self.rows(44)),2)
        source_row=next(row for row in self.rows(43) if row['part']==origin.part.number)
        self.assertEqual((source_row['pending'],source_row['credit']), (0,29))

    def test_permissions_closed_periods_and_stale_requests(self):
        origin=self.line(100)
        user=get_user_model().objects.create_user(username='no-plan')
        with self.assertRaises(PermissionDenied):move(user,origin.pk,{})
        with self.assertRaises(ValidationError):self.move(origin,42)
        ClosedPeriod.objects.create(date=timezone.localdate(),reason='closed',actor=self.actor)
        with self.assertRaises(ValidationError):self.move(origin)
        self.assertEqual(WeekTransfer.objects.count(),0)

    def test_correction_restores_pending_in_working_week(self):
        origin=self.line(100);self.move(origin)
        event=self.pack(origin,100)
        self.assertEqual(self.rows(44),[])
        s.correct(self.actor,event.pk,40,'Correction',uuid.uuid4())
        self.assertTrue(self.rows(43)[0]['carry_history'])
        self.assertEqual(self.rows(44)[0]['pending'],60)

    def test_api_exposes_work_week_for_selectors(self):
        origin=self.line(100);key=str(uuid.uuid4())
        response=self.client.post(f'/api/demands/{origin.pk}/next-week/',{'key':key,'year':2026,'week':43},format='json')
        self.assertEqual(response.status_code,200)
        catalog=self.client.get('/api/catalog/').data
        self.assertIn({'year':2026,'week':44},catalog['work_weeks'])
        response=self.client.post(f'/api/demands/{origin.pk}/next-week/',{'key':key,'year':2026,'week':43},format='json')
        self.assertEqual(response.status_code,200)
        self.assertEqual(WeekTransfer.objects.count(),1)

    def test_surplus_does_not_steal_unreleased_group_capacity(self):
        origin=self.line(100);source=self.pack(origin,150)
        waiting=self.line(100,44);self.pack(waiting,150,False)
        target=self.line(100,44)
        self.move(origin)
        row=self.rows(44)[0]
        self.assertEqual(row['packing_pending'],0)
        self.assertEqual(s.applied(target),50)
        self.assertEqual(s.available(source),0)
        self.assertEqual(row['pending_release'],150)

    def test_export_preserves_working_and_original_week(self):
        from io import BytesIO
        from openpyxl import load_workbook
        origin=self.line(100);self.move(origin)
        response=self.client.get('/api/export/',{'year':2026,'week':44,'order_state':'all'})
        self.assertEqual(response.status_code,200)
        rows=list(load_workbook(BytesIO(response.content)).active.values)
        self.assertEqual(rows[0][-1],'Trasladado desde')
        self.assertEqual(rows[1][-1],'2026/S43')
        self.assertEqual(rows[1][3],44)

    def test_partial_capture_completes_origin_then_remains_on_target(self):
        origin=self.line(100);target=self.line(200,44);self.move(origin)
        self.pack(origin,150)
        self.assertEqual(s.applied(origin),100);self.assertEqual(s.applied(target),50)
        self.assertEqual(self.rows(43)[0]['pending'],0)
        self.assertEqual(self.rows(44)[0]['pending'],150)
        all_rows=self.rows()
        self.assertEqual(sum(row['packed'] for row in all_rows),150)
        self.assertEqual(sum(row['quantity'] for row in all_rows),300)
