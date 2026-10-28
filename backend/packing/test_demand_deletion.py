import uuid
from datetime import date,datetime,time as dt_time,timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from .models import Program, Demand, Part, BalanceGroup, Audit, Employee, Shift
from . import services


class DemandDeletionTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_superuser(username='demand-delete-test',password='synthetic-only')
        self.client=APIClient();self.client.force_authenticate(self.user)
        group=BalanceGroup.objects.create(name='DELETE TEST')
        part=Part.objects.create(number='DELETE-TEST',customer='DELETE TEST',universe_id=str(uuid.uuid4()),provisional=False,attributes={'active':True})
        year=timezone.localdate().year
        program=Program.objects.create(group=group,client='DELETE TEST',year=year,week=43,starts_on=date.fromisocalendar(year,43,1),ends_on=date.fromisocalendar(year,43,7),reference='DELETE-TEST')
        self.line=Demand.objects.create(program=program,part=part,reference='ORDER-1',original=100,quantity=100)

    def test_delete_unrecorded_demand_keeps_audit_evidence(self):
        response=self.client.delete(f'/api/demands/{self.line.pk}/',{'reason':'Orden duplicada'},format='json')
        self.assertEqual(response.status_code,200,response.data)
        self.line.refresh_from_db()
        self.assertTrue(self.line.archived)
        self.assertFalse(services.demand_queryset(self.user,{}).filter(pk=self.line.pk).exists())
        event=Audit.objects.get(kind='delete_demand')
        self.assertEqual(event.reason,'Orden duplicada')
        self.assertEqual(event.data['demand']['part'],'DELETE-TEST')

    def test_demand_with_capture_is_removed_from_orders_and_history_is_preserved(self):
        self.line.program.published=True;self.line.program.save()
        Shift.objects.create(code='A');Employee.objects.create(payroll='DELETE-P',name='Synthetic')
        effective=timezone.make_aware(datetime.combine(timezone.localdate()-timedelta(days=1),dt_time(10)),timezone.get_current_timezone())
        services.capture(self.user,{'key':str(uuid.uuid4()),'demand':self.line.pk,'quantity':10,'effective_at':effective.isoformat(),'operational_date':str(timezone.localdate()),'shift':'A','packer':'DELETE-P','inspector':'DELETE-I'})
        response=self.client.delete(f'/api/demands/{self.line.pk}/',{'reason':'Test'},format='json')
        self.assertEqual(response.status_code,200,response.data)
        self.line.refresh_from_db()
        self.assertTrue(self.line.archived)
        self.assertTrue(Audit.objects.filter(kind='delete_demand').exists())
        history=self.client.get('/api/captures/')
        self.assertEqual(len(history.data),1)
