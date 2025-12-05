#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Collecting static files..."
echo yes | python manage.py collectstatic

echo "Starting Daphne..."
daphne -b 0.0.0.0 -p 8000 klikdat_django.asgi:application
