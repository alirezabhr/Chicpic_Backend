#!/bin/sh

echo 'Waiting for postgres...'

while ! nc -z $DB_HOST $DB_PORT; do
    sleep 0.1
done

echo 'Postgres started'

echo 'Running migrations...'
python manage.py migrate

echo 'Collecting static files...'
python manage.py collectstatic --no-input

exec "$@"