#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Waiting for database..."
python << END
import sys
import time
import psycopg2
import os

max_retries = 60
retry_count = 0

while retry_count < max_retries:
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DATABASE_NAME', 'polls'),
            user=os.getenv('DATABASE_USERNAME', 'myprojectuser'),
            password=os.getenv('DATABASE_PASSWORD', 'password'),
            host=os.getenv('DATABASE_HOST', 'db'),
            port=os.getenv('DATABASE_PORT', '5432')
        )
        conn.close()
        print("Database is ready!")
        sys.exit(0)
    except psycopg2.OperationalError:
        retry_count += 1
        time.sleep(1)

print("Database connection failed after {} retries".format(max_retries))
sys.exit(1)
END

echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Collecting static files..."
echo yes | python manage.py collectstatic

echo "Starting Daphne..."
daphne -b 0.0.0.0 -p 8000 klikdat_django.asgi:application
