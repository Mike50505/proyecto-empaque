import os
import secrets
import socket
import subprocess
import time
import urllib.request
import tempfile
from openpyxl import Workbook
from pathlib import Path
from datetime import date
from django.test import LiveServerTestCase,override_settings
from django.contrib.auth import get_user_model
from .models import *

@override_settings(ALLOWED_HOSTS=['localhost','127.0.0.1','testserver'])
class BrowserAcceptance(LiveServerTestCase):
    def test_browser_full_flow(self):
        if os.getenv('RUN_BROWSER_TESTS')!='1': self.skipTest('Activar RUN_BROWSER_TESTS=1 para navegador real.')
        root=Path(__file__).resolve().parents[2]
        password=secrets.token_urlsafe(24)
        get_user_model().objects.create_superuser(username='synthetic-ui',password=password)
        g=BalanceGroup.objects.create(name='SINTÉTICO · UI')
        part=Part.objects.create(number='TEST-UI-0001',customer='CLIENTE SINTÉTICO',diameter='A - 3/8',universe_id='synthetic-universe-1',provisional=False,attributes={'active':True})
        Part.objects.create(number='TEST-FOREIGN',customer='FOREIGN CUSTOMER',universe_id='synthetic-universe-foreign',provisional=False,attributes={'active':True})
        p=Program.objects.create(group=g,client='CLIENTE SINTÉTICO',scope='DESTINO DE PRUEBA',year=2026,week=43,starts_on=date.fromisocalendar(2026,43,1),ends_on=date.fromisocalendar(2026,43,7),reference='SINTETICO-UI',published=True)
        Demand.objects.create(program=p,part=part,reference='1',original=300,quantity=300,priority=1)
        delete_program=Program.objects.create(group=g,client='FOREIGN CUSTOMER',scope='DELETE TEST',year=2026,week=45,starts_on=date.fromisocalendar(2026,45,1),ends_on=date.fromisocalendar(2026,45,7),reference='DELETE-ME',published=False)
        Demand.objects.create(program=delete_program,part=Part.objects.get(number='TEST-FOREIGN'),reference='DELETE-ORDER',original=25,quantity=25)
        for code in ['A','B']: Shift.objects.create(code=code)
        Employee.objects.create(payroll='TEST-P',name='Empacador sintético')
        Employee.objects.create(payroll='TEST-I',name='Inspector sintético',inspector=True)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
        env={**os.environ,'MESA_API_TARGET':self.live_server_url,'MESA_E2E_URL':f'http://127.0.0.1:{port}','MESA_E2E_PASSWORD':password}
        temp_import=tempfile.NamedTemporaryFile(suffix='.xlsx',delete=False)
        temp_import.close()
        workbook=Workbook();sheet=workbook.active;sheet.title='Programa'
        sheet.append(['cliente','destino_o_ambito','semana_programa','numero_parte','cantidad_programada'])
        for i in range(10):sheet.append(['CLIENTE SINTÉTICO','DESTINO DE PRUEBA',44,part.number,100])
        workbook.save(temp_import.name)
        env['MESA_E2E_IMPORT_FILE']=temp_import.name
        bad_import=tempfile.NamedTemporaryFile(suffix='.xlsx',delete=False);bad_import.close()
        bad_book=Workbook();bad_sheet=bad_book.active;bad_sheet.title='Programa'
        bad_sheet.append(['cliente','destino_o_ambito','semana_programa','numero_parte','cantidad_programada'])
        bad_sheet.append(['FOREIGN CUSTOMER','DESTINO DE PRUEBA',44,part.number,100])
        bad_book.save(bad_import.name);env['MESA_E2E_BAD_IMPORT_FILE']=bad_import.name
        log=root/'private'/'e2e-vite.log';log.parent.mkdir(exist_ok=True)
        with log.open('w') as stream:
            server=subprocess.Popen(['node','node_modules/vite/bin/vite.js','--host','127.0.0.1','--port',str(port),'--strictPort'],cwd=root/'frontend',env=env,stdout=stream,stderr=stream,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try:
                for _ in range(60):
                    try:
                        urllib.request.urlopen(env['MESA_E2E_URL'],timeout=1);break
                    except Exception:time.sleep(.2)
                with self.settings(CSRF_TRUSTED_ORIGINS=[env['MESA_E2E_URL']]):
                    result=subprocess.run(['node','e2e.mjs'],cwd=root/'frontend',env=env,capture_output=True,text=True,timeout=120)
                self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
                self.assertEqual(Capture.objects.filter(voided=False).count(),3)
            finally:
                server.terminate();server.wait(timeout=10)
                Path(temp_import.name).unlink(missing_ok=True)
                Path(bad_import.name).unlink(missing_ok=True)
