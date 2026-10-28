import uuid
from datetime import date, datetime, time, timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from .models import BalanceGroup, Part, Program, Demand, Capture, Shift, OpeningBalance, Allocation
from . import services as s
from .surplus import inventory


class SurplusInventoryTests(TestCase):
    def setUp(self):
        self.actor=get_user_model().objects.create_superuser(username='inventory-test',password=None)
        self.group=BalanceGroup.objects.create(name='SYNTHETIC')
        self.part=Part.objects.create(number='EXCESS-01',customer='LENNOX 1',universe_id=str(uuid.uuid4()),provisional=False)
        Shift.objects.create(code='A')
        self.client=APIClient();self.client.force_authenticate(self.actor)

    def line(self,qty,week=43,scope='SLP'):
        program=Program.objects.create(group=self.group,client=self.part.customer,scope=scope,year=2026,week=week,starts_on=date.fromisocalendar(2026,week,1),ends_on=date.fromisocalendar(2026,week,7),reference=str(uuid.uuid4()),published=True)
        return Demand.objects.create(program=program,part=self.part,reference=str(uuid.uuid4()),original=qty,quantity=qty)

    def pack(self,line,qty):
        day=timezone.localdate()-timedelta(days=1)
        return s.capture(self.actor,{'key':str(uuid.uuid4()),'demand':line.pk,'quantity':qty,'effective_at':timezone.make_aware(datetime.combine(day,time(10))).isoformat(),'operational_date':str(day),'packer':'00007','inspector':'00045','accept_excess':True})

    def test_surplus_is_separate_and_never_moves_to_next_week(self):
        origin=self.line(100);target=self.line(200,44)
        event=self.pack(origin,130)
        result=self.client.get('/api/surplus/')
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.data['total'],30)
        row=result.data['rows'][0]
        self.assertEqual((row['part'],row['week'],row['quantity'],row['inspector']),('EXCESS-01',43,30,'00045'))
        self.assertEqual(s.applied(origin),100);self.assertEqual(s.applied(target),0)
        inventory(self.actor,{})
        self.assertEqual(s.available(event),30);self.assertEqual(s.applied(target),0)

    def test_old_carry_metadata_does_not_move_balances_or_new_captures(self):
        origin=self.line(100);origin.carry_to=date.fromisocalendar(2026,44,1);origin.save()
        target=self.line(200,44)
        event=self.pack(origin,130)
        self.assertEqual(s.applied(origin),100);self.assertEqual(s.applied(target),0)
        self.assertEqual(s.available(event),30)
        self.assertEqual([r['id'] for r in s.balance(self.actor,{'year':'2026','week':'43'})['rows']],[origin.pk])
        self.assertEqual([r['id'] for r in s.balance(self.actor,{'year':'2026','week':'44'})['rows']],[target.pk])
        self.assertEqual(self.client.post(f'/api/demands/{origin.pk}/next-week/',{},format='json').status_code,404)

    def test_publication_does_not_consume_existing_surplus(self):
        origin=self.line(100);origin.carry_to=date.fromisocalendar(2026,44,1);origin.save()
        event=self.pack(origin,130);target=self.line(200,44)
        target.program.published=False;target.program.save()
        result=self.client.post(f'/api/programs/{target.program_id}/publication/',{'published':True},format='json')
        self.assertEqual(result.status_code,200,result.data)
        self.assertEqual(s.available(event),30);self.assertEqual(s.applied(target),0)

    def test_inventory_uses_available_not_total_and_keeps_archived_sources(self):
        origin=self.line(100);event=self.pack(origin,150);target=self.line(100,44)
        s.transfer(self.actor,event.pk,target.pk,20,'Historical explicit allocation')
        origin.archived=True;origin.save()
        data=inventory(self.actor,{})
        self.assertEqual(data['total'],30)
        self.assertTrue(data['rows'][0]['archived'])

    def test_opening_balances_and_filters(self):
        origin=self.line(100)
        opening=OpeningBalance.objects.create(demand=origin,applied=100,credit=25,cutoff=timezone.now())
        Allocation.objects.create(opening=opening,demand=origin,quantity=100)
        self.assertEqual(inventory(self.actor,{'week':'43','client':'LENNOX 1','scope':'SLP','search':'EXCESS'})['total'],25)
        self.assertEqual(inventory(self.actor,{'week':'44'})['total'],0)
        self.assertEqual(inventory(self.actor,{'scope':'OTHER'})['rows'],[])

    def test_pending_and_voided_captures_are_not_available(self):
        line=self.line(100);event=self.pack(line,130)
        event.released=False;event.save()
        self.assertEqual(inventory(self.actor,{})['rows'],[])
        event.released=True;event.voided=True;event.save()
        self.assertEqual(inventory(self.actor,{})['total'],0)

    def test_consult_permission_is_required(self):
        reader=get_user_model().objects.create_user('reader')
        self.client.force_authenticate(reader)
        self.assertEqual(self.client.get('/api/surplus/').status_code,403)
        reader.user_permissions.add(Permission.objects.get(codename='consult'))
        self.client.force_authenticate(get_user_model().objects.get(pk=reader.pk))
        self.assertEqual(self.client.get('/api/surplus/').status_code,200)
