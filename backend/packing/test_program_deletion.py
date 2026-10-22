import tempfile
import uuid
from datetime import date,datetime,time as dt_time,timedelta
from io import BytesIO
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError
from openpyxl import Workbook
from .models import Program, Demand, Part, BalanceGroup, Audit, Employee, Shift, OpeningBalance, Revision, ClosedPeriod
from . import services, importing


class ProgramDeletionTests(TestCase):
    def setUp(self):
        media=tempfile.TemporaryDirectory();self.addCleanup(media.cleanup)
        self.enterContext(override_settings(MEDIA_ROOT=media.name))
        self.user=get_user_model().objects.create_superuser(username='delete-test',password='synthetic-only')
        self.client=APIClient();self.client.force_authenticate(self.user)
        self.group=BalanceGroup.objects.create(name='LENNOX 1')
        self.part=Part.objects.create(number='DELETE-TEST',customer='LENNOX 1',universe_id=str(uuid.uuid4()),provisional=False,attributes={'active':True})
        self.program,self.line=self.make_program()

    def make_program(self,published=False,client='LENNOX 1'):
        year=timezone.localdate().year
        program=Program.objects.create(group=self.group,client=client,year=year,week=43,starts_on=date.fromisocalendar(year,43,1),ends_on=date.fromisocalendar(year,43,7),reference=str(uuid.uuid4()),published=published)
        line=Demand.objects.create(program=program,part=self.part,reference='ORDER-1',original=100,quantity=100)
        return program,line

    def review(self,program=None):
        return self.client.get(f'/api/programs/{(program or self.program).pk}/')

    def delete(self,program=None,review=None,reason='Carga incorrecta'):
        program=program or self.program
        info=review if review is not None else self.review(program).data
        return self.client.delete(f'/api/programs/{program.pk}/',{'reason':reason,'confirmation':info['confirmation']},format='json')

    def test_delete_program_and_orders_keeps_catalog_and_audit(self):
        Demand.objects.create(program=self.program,part=self.part,reference='ORDER-2',original=30,quantity=30)
        reviewed=self.review().data
        self.assertEqual(reviewed['order_count'],2);self.assertEqual(reviewed['quantity'],130)
        self.assertTrue(reviewed['can_delete'])
        response=self.delete(review=reviewed)
        self.assertEqual(response.status_code,200,response.data)
        self.assertEqual(response.data['orders_deleted'],2)
        self.assertFalse(Program.objects.exists());self.assertFalse(Demand.objects.exists())
        self.assertTrue(Part.objects.filter(pk=self.part.pk).exists())
        audit=Audit.objects.get(kind='delete_program')
        self.assertEqual(audit.reason,'Carga incorrecta');self.assertEqual(len(audit.data['orders']),2)

    def test_published_incompatible_program_without_history_can_be_removed(self):
        self.program.published=True;self.program.client='RHEEM TRANSFERENCIA';self.program.save()
        self.assertEqual(self.delete().status_code,200)

    def test_only_planning_can_review_or_delete(self):
        reader=get_user_model().objects.create_user(username='delete-reader')
        self.client.force_authenticate(reader)
        self.assertEqual(self.review().status_code,403)
        self.assertEqual(self.client.delete(f'/api/programs/{self.program.pk}/',{},format='json').status_code,403)
        self.assertTrue(Program.objects.filter(pk=self.program.pk).exists())

    def test_reason_and_review_confirmation_are_required(self):
        self.assertEqual(self.delete(reason=' ').status_code,400)
        response=self.client.delete(f'/api/programs/{self.program.pk}/',{'reason':'No confirmation'},format='json')
        self.assertEqual(response.status_code,400);self.assertTrue(Program.objects.exists())

    def test_orders_added_after_review_cannot_be_deleted_silently(self):
        reviewed=self.review().data
        Demand.objects.create(program=self.program,part=self.part,reference='NEW-ORDER',original=5,quantity=5)
        response=self.delete(review=reviewed)
        self.assertEqual(response.status_code,400);self.assertEqual(Demand.objects.count(),2)
        self.assertFalse(Audit.objects.filter(kind='delete_program').exists())

    def test_capture_record_blocks_deletion_even_when_voided(self):
        self.program.published=True;self.program.save()
        Shift.objects.create(code='A');Employee.objects.create(payroll='DELETE-P',name='Synthetic')
        reviewed=self.review().data
        effective=timezone.make_aware(datetime.combine(timezone.localdate()-timedelta(days=1),dt_time(10)),timezone.get_current_timezone())
        event=services.capture(self.user,{'key':str(uuid.uuid4()),'demand':self.line.pk,'quantity':10,'effective_at':effective.isoformat(),'operational_date':str(timezone.localdate()),'shift':'A','packer':'DELETE-P','inspector':''})
        self.assertEqual(self.delete(review=reviewed).status_code,400)
        event.voided=True;event.save()
        self.assertFalse(self.review().data['can_delete'])
        self.assertEqual(self.delete().status_code,400)
        self.assertTrue(Program.objects.exists())

    def test_opening_balance_and_revisions_block_deletion(self):
        opening=OpeningBalance.objects.create(demand=self.line,cutoff=timezone.now())
        self.assertFalse(self.review().data['can_delete']);self.assertEqual(self.delete().status_code,400)
        opening.delete()
        Revision.objects.create(demand=self.line,before=100,after=100,reason='Revision',actor=self.user)
        self.assertEqual(self.delete().status_code,400)

    def test_closed_operating_date_blocks_deletion(self):
        ClosedPeriod.objects.create(date=timezone.localdate(),reason='Closed',actor=self.user)
        self.assertFalse(self.review().data['can_delete']);self.assertEqual(self.delete().status_code,400)

    def test_applied_import_keeps_evidence_and_cannot_resurrect_deleted_program(self):
        workbook=Workbook();sheet=workbook.active;sheet.title='Programa'
        sheet.append(['cliente','destino_o_ambito','semana_programa','numero_parte','cantidad_programada'])
        sheet.append(['LENNOX 1','',44,self.part.number,25])
        stream=BytesIO();workbook.save(stream)
        batch=importing.preview(self.user,SimpleUploadedFile('delete-import.xlsx',stream.getvalue()),'new',{'reason':'Delete import test'})
        importing.commit(self.user,batch.pk,publish=True)
        batch.refresh_from_db();program=Program.objects.get(pk=batch.preview['program_ids'][0]);program_id=program.pk
        self.assertEqual(self.delete(program).status_code,200)
        result=importing.result(batch)
        self.assertEqual(result['missing_programs'],[program_id]);self.assertFalse(result['visible_in_capture'])
        importing.commit(self.user,batch.pk)
        self.assertFalse(Program.objects.filter(pk=program_id).exists())
        with self.assertRaises(ValidationError):importing.commit(self.user,batch.pk,publish=True)
