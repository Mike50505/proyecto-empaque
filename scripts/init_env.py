from pathlib import Path
import secrets
root=Path(__file__).resolve().parents[1]
path=root/'.env'
if path.exists():
    print('.env existente conservado.')
else:
    text=(root/'.env.example').read_text(encoding='utf-8')
    text=text.replace('DJANGO_SECRET_KEY=','DJANGO_SECRET_KEY='+secrets.token_urlsafe(48),1).replace('POSTGRES_PASSWORD=','POSTGRES_PASSWORD='+secrets.token_urlsafe(32),1)
    path.write_text(text,encoding='utf-8');print('.env generado con secretos aleatorios; configura UNIVERSO_TOKEN en el servidor.')
