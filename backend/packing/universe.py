"""Contrato v1 comprobado en el proyecto hermano docs/API.md. Solo lectura."""
import json
import os
from urllib.parse import urlparse, urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import Part, IntegrationState
from .services import lock_ledger

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None

def fetch(path):
    base=os.getenv('UNIVERSO_URL','https://universo.mesaramos.com').rstrip('/')
    if urlparse(base).scheme!='https': raise ValidationError('Universo requiere HTTPS.')
    token=os.getenv('UNIVERSO_TOKEN','')
    if not token: raise ValidationError('Falta configurar UNIVERSO_TOKEN en el servidor.')
    if not path.startswith('/api/v1/'): raise ValidationError('Ruta fuera del contrato autorizado.')
    try:
        request=Request(base+path, headers={'Authorization':'Bearer '+token,'Accept':'application/json','User-Agent':'Empaques-MESA/1.0'})
        with build_opener(NoRedirect).open(request,timeout=30) as response:
            return json.loads(response.read(10*1024*1024))
    except HTTPError as exc: raise ValidationError(f'Universo respondió HTTP {exc.code}; el catálogo local sigue disponible.')
    except (URLError,ValueError,TimeoutError): raise ValidationError('Universo no disponible o respuesta inválida; se conserva el catálogo local.')

def upsert(item):
    # Los eventos de cambios guardan IDs de catálogos; no se asumen nombres.
    defaults={'number':item['part_number'],'diameter':str(item.get('diameter') or ''),'attributes':item,'provisional':False,'synced_at':timezone.now()}
    if 'customer' in item: defaults['customer']=item['customer'] or ''
    if 'destination' in item: defaults['scope']=item['destination'] or ''
    Part.objects.update_or_create(universe_id=str(item['id']),defaults=defaults)

def sync(full=False):
    state,_=IntegrationState.objects.get_or_create(name='universo')
    try:
        catalogs=fetch('/api/v1/catalogs/')
        customer_names={str(item['id']):item['name'] for item in catalogs['customers']}
        destination_names={str(item['id']):item['name'] for item in catalogs['destinations']}
        if full or not state.cursor:
            initial=fetch('/api/v1/bootstrap/')
            page=1
            while True:
                result=fetch('/api/v1/parts/?'+urlencode({'page':page,'page_size':200}))
                with transaction.atomic():
                    lock_ledger()
                    for item in result['results']: upsert(item)
                if not result.get('next'): break
                page+=1
            state.cursor=initial['changes_cursor']; state.save(update_fields=['cursor'])
        while True:
            result=fetch('/api/v1/changes/?'+urlencode({'cursor':state.cursor,'limit':200}))
            with transaction.atomic():
                lock_ledger()
                for event in result['results']:
                    item={**event['part'],'id':event['part_id']}
                    # Change images contain FK IDs, while /parts/ contains names.
                    # Resolve the names rather than retaining a stale customer.
                    if 'customer' not in item:
                        customer=customer_names.get(str(item.get('customer_id')))
                        if customer is None:
                            upsert(fetch(f"/api/v1/parts/{event['part_id']}/"))
                            continue
                        item['customer']=customer
                    if 'destination' not in item:
                        destination_id=item.get('destination_id')
                        if destination_id is not None and str(destination_id) not in destination_names:
                            upsert(fetch(f"/api/v1/parts/{event['part_id']}/"))
                            continue
                        item['destination']=destination_names.get(str(destination_id),'')
                    upsert(item)
                state.cursor=result['next_cursor']; state.last_sync=timezone.now(); state.error=''; state.save()
            if not result['has_more']: break
    except ValidationError as exc:
        state.error=str(exc.detail)[:200]; state.save(update_fields=['error']); raise
    return {'parts':Part.objects.filter(provisional=False).count(),'last_sync':state.last_sync}
