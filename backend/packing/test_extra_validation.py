import uuid
from datetime import datetime, time, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from .models import Part, ExtraCapture, Shift, Audit


class ExtraPartValidation(TestCase):
    def setUp(self):
        self.actor=get_user_model().objects.create_superuser('extra-validation',password='Synthetic-only-2026!')
        self.client=APIClient();self.client.force_authenticate(self.actor)
        self.part=Part.objects.create(number='VALID-001',customer='LENNOX 1',scope='SLP',universe_id=str(uuid.uuid4()),provisional=False,attributes={'active':True})
        for code in ('A','B'):Shift.objects.get_or_create(code=code)
        day=timezone.localdate()-timedelta(days=1)
        effective=timezone.make_aware(datetime.combine(day,time(10)))
        self.payload={'key':str(uuid.uuid4()),'part_number':self.part.number,'part_id':self.part.pk,'quantity':10,'effective_at':effective.isoformat(),'operational_date':str(day),'packer':'TEST-P','inspector':'TEST-I'}

    def test_valid_part_and_idempotent_retry(self):
        response=self.client.post('/api/extras/',self.payload,format='json')
        self.assertEqual(response.status_code,201,response.data)
        self.assertEqual(ExtraCapture.objects.get().part_number,'VALID-001')
        self.assertEqual(self.client.post('/api/extras/',self.payload,format='json').status_code,201)
        self.assertEqual(ExtraCapture.objects.count(),1)

    def test_unknown_part_cannot_create_capture_or_catalog_entry(self):
        count=Part.objects.count()
        response=self.client.post('/api/extras/',{**self.payload,'part_number':'DOES-NOT-EXIST','part_id':None},format='json')
        self.assertEqual(response.status_code,400,response.data)
        self.assertEqual(ExtraCapture.objects.count(),0);self.assertEqual(Part.objects.count(),count)
        self.assertFalse(Audit.objects.filter(kind='extra_capture').exists())

    def test_inactive_provisional_unconfirmed_and_missing_customer_rejected(self):
        for change in ({'attributes':{'active':False}},{'provisional':True},{'universe_id':None},{'customer':''}):
            with self.subTest(change=change):
                Part.objects.filter(pk=self.part.pk).update(attributes={'active':True},provisional=False,universe_id=str(uuid.uuid4()),customer='LENNOX 1')
                Part.objects.filter(pk=self.part.pk).update(**change)
                response=self.client.post('/api/extras/',self.payload,format='json')
                self.assertEqual(response.status_code,400,response.data)
                self.assertFalse(ExtraCapture.objects.exists())

    def test_forged_identity_and_ambiguous_number_rejected(self):
        other=Part.objects.create(number='VALID-002',customer='RHEEM',universe_id=str(uuid.uuid4()),provisional=False)
        self.assertEqual(self.client.post('/api/extras/',{**self.payload,'part_id':other.pk},format='json').status_code,400)
        other.number=self.part.number;other.save()
        self.assertEqual(self.client.post('/api/extras/',{**self.payload,'part_id':None},format='json').status_code,400)
        self.assertFalse(ExtraCapture.objects.exists())
        self.assertEqual(self.client.post('/api/extras/',self.payload,format='json').status_code,201)

    def test_exact_number_is_canonicalized_and_rechecked_at_confirmation(self):
        response=self.client.post('/api/extras/',{**self.payload,'part_number':' valid-001 ','part_id':None},format='json')
        self.assertEqual(response.status_code,201,response.data)
        self.assertEqual(ExtraCapture.objects.get().part_number,'VALID-001')
        self.part.attributes={'active':False};self.part.save()
        rejected=self.client.post('/api/extras/',{**self.payload,'key':str(uuid.uuid4())},format='json')
        self.assertEqual(rejected.status_code,400);self.assertEqual(ExtraCapture.objects.count(),1)
