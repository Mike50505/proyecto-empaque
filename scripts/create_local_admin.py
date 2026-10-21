"""Primer acceso local sin contraseña predeterminada. No imprime secretos."""
import os
import secrets
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
if not get_user_model().objects.filter(is_superuser=True).exists():
    password=secrets.token_urlsafe(20)
    get_user_model().objects.create_superuser(username='miguel',password=password)
    folder=root/'private';folder.mkdir(exist_ok=True)
    (folder/'primer_acceso.txt').write_text('Empaques MESA — acceso local\nUsuario: miguel\nContraseña temporal: '+password+'\nCámbiala desde /admin/password_change/.\n',encoding='utf-8')
    print('Acceso generado en private/primer_acceso.txt; no se ha mostrado la contraseña.')
else: print('Ya existe administrador; no se modificó su acceso.')
