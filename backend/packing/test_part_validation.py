import tempfile
import uuid
from io import BytesIO
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from openpyxl import Workbook
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError
from .models import Part, Program, Demand, BalanceGroup, IntegrationState
from . import importing, services, universe
from .part_validation import resolve_part


class PartCustomerValidation(TestCase):
    def setUp(self):
        media=tempfile.TemporaryDirectory();self.addCleanup(media.cleanup)
        self.enterContext(override_settings(MEDIA_ROOT=media.name))
        self.user=get_user_model().objects.create_superuser(username='catalog-test',password='synthetic-only')
        self.client=APIClient();self.client.force_authenticate(self.user)
        self.part=Part.objects.create(number='LEN-001',customer='LENNOX 1',universe_id=str(uuid.uuid4()),provisional=False,attributes={'active':True})

    def workbook(self,customer='LENNOX 1',number='LEN-001'):
        book=Workbook();sheet=book.active;sheet.title='Programa'
        sheet.append(['cliente','destino_o_ambito','semana_programa','numero_parte','cantidad_programada'])
        sheet.append([customer,'',43,number,100])
        stream=BytesIO();book.save(stream)
        return SimpleUploadedFile('catalog-test.xlsx',stream.getvalue())

    def preview(self,customer='LENNOX 1',number='LEN-001',**mapping):
        return importing.preview(self.user,self.workbook(customer,number),'new',{'reason':'Catalog validation',**mapping})

    def test_wrong_customer_is_blocking_in_excel_and_cannot_be_committed(self):
        batch=self.preview('RHEEM TRANSFERENCIA')
        self.assertTrue(any('LENNOX 1' in issue['message'] and issue['severity']=='blocking' for issue in batch.preview['issues']))
        with self.assertRaises(ValidationError): importing.commit(self.user,batch.pk,publish=True)
        self.assertEqual(Demand.objects.count(),0);self.assertEqual(Program.objects.count(),0)

    def test_explicit_part_mapping_and_provisional_flag_cannot_bypass_customer(self):
        batch=self.preview('RHEEM TRANSFERENCIA',part_resolutions={'2':self.part.pk},approve_provisional=True)
        self.assertTrue(any(issue['severity']=='blocking' for issue in batch.preview['issues']))
        with self.assertRaises(ValidationError): importing.commit(self.user,batch.pk)

    def test_unknown_part_cannot_be_created_using_provisional_flag(self):
        batch=self.preview(number='UNKNOWN',approve_provisional=True)
        with self.assertRaises(ValidationError): importing.commit(self.user,batch.pk)
        self.assertFalse(Part.objects.filter(number='UNKNOWN').exists())

    def test_provisional_and_inactive_parts_cannot_be_used(self):
        self.part.provisional=True;self.part.save()
        with self.assertRaises(ValidationError): resolve_part(self.part.number,self.part.customer)
        self.part.provisional=False;self.part.attributes={'active':False};self.part.save()
        with self.assertRaises(ValidationError): resolve_part(self.part.number,self.part.customer)

    def test_manual_mismatch_rolls_back_the_entire_program(self):
        response=self.client.post('/api/programs/',{'client':'RHEEM TRANSFERENCIA','week':43,'lines':[{'part':self.part.pk,'quantity':100}]},format='json')
        self.assertEqual(response.status_code,400,response.data)
        self.assertIn('LENNOX 1',str(response.data));self.assertEqual(Program.objects.count(),0)

    def test_manual_valid_customer_is_canonicalized(self):
        response=self.client.post('/api/programs/',{'client':' lennox 1 ','week':43,'lines':[{'part':self.part.pk,'quantity':100}]},format='json')
        self.assertEqual(response.status_code,201,response.data)
        self.assertEqual(Program.objects.get(pk=response.data['id']).client,'LENNOX 1')

    def test_commit_revalidates_a_previously_accepted_preview(self):
        batch=self.preview()
        self.assertFalse(batch.preview['issues'])
        self.part.customer='OTHER CUSTOMER';self.part.save(update_fields=['customer'])
        with self.assertRaises(ValidationError): importing.commit(self.user,batch.pk,publish=True)
        self.assertEqual(Demand.objects.count(),0);self.assertEqual(Program.objects.count(),0)

    def test_legacy_mismatch_cannot_be_published_or_captured(self):
        batch=self.preview();importing.commit(self.user,batch.pk)
        line=Demand.objects.select_related('program').get()
        line.program.client='RHEEM TRANSFERENCIA';line.program.save()
        response=self.client.post(f'/api/programs/{line.program_id}/publication/',{'published':True},format='json')
        self.assertEqual(response.status_code,400)
        line.program.published=True;line.program.save()
        with self.assertRaises(ValidationError): services.capture(self.user,{'key':str(uuid.uuid4()),'demand':line.pk})
        row=services.balance(self.user,{})['rows'][0]
        self.assertIn('LENNOX 1',row['catalog_error'])

    def test_equal_part_numbers_do_not_override_the_requested_customer(self):
        other=Part.objects.create(number=self.part.number,customer='RHEEM TRANSFERENCIA',universe_id=str(uuid.uuid4()),provisional=False,attributes={'active':True})
        self.assertEqual(resolve_part(self.part.number,'LENNOX 1').pk,self.part.pk)
        self.assertEqual(resolve_part(self.part.number,'RHEEM TRANSFERENCIA').pk,other.pk)
        with self.assertRaises(ValidationError): resolve_part(self.part.number,'RHEEM TRANSFERENCIA',self.part.pk)

    def test_universe_change_customer_ids_refresh_the_customer_name(self):
        IntegrationState.objects.create(name='universo',cursor='old')
        def fetch(path):
            if path=='/api/v1/catalogs/':
                return {'customers':[{'id':9,'name':'RHEEM TRANSFERENCIA'}],'destinations':[]}
            if path.startswith('/api/v1/changes/'):
                return {'results':[{'part_id':self.part.universe_id,'part':{'part_number':self.part.number,'customer_id':9,'destination_id':None,'active':True}}],'next_cursor':'new','has_more':False}
            raise AssertionError(path)
        with patch('packing.universe.fetch',side_effect=fetch): universe.sync()
        self.part.refresh_from_db();self.assertEqual(self.part.customer,'RHEEM TRANSFERENCIA')
        with self.assertRaises(ValidationError): resolve_part(self.part.number,'LENNOX 1')
        self.assertEqual(IntegrationState.objects.get(name='universo').cursor,'new')
