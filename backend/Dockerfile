FROM python:3.13-slim
WORKDIR /app
COPY requirements.lock.txt .
RUN pip install --no-cache-dir -r requirements.lock.txt
COPY backend ./backend
WORKDIR /app/backend
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py bootstrap && python manage.py collectstatic --noinput && waitress-serve --listen=0.0.0.0:8000 config.wsgi:application"]
