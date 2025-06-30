#!/bin/sh
echo "Waiting for postgres..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"
python -c 'import time; time.sleep(2); from database import Base, engine; from models import *; Base.metadata.create_all(bind=engine)'
exec "$@"
