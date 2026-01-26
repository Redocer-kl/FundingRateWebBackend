#!/bin/sh
set -e

# defaults
: "${DB_HOST:=db}"
: "${DB_PORT:=5432}"
: "${RUN_MIGRATIONS:=0}"

# Ожидание Postgres (требуется pg_isready в образе)
if [ "$DB_ENGINE" = "django.db.backends.postgresql" ]; then
  echo "Waiting for Postgres at $DB_HOST:$DB_PORT ..."
  until pg_isready -h "$DB_HOST" -p "$DB_PORT" >/dev/null 2>&1; do
    sleep 1
  done
fi

# Выполняем миграции и collectstatic только если явно разрешено (только web)
if [ "$RUN_MIGRATIONS" = "1" ]; then
  echo "Running migrations..."
  python manage.py migrate --noinput
  echo "Collectstatic..."
  python manage.py collectstatic --noinput --clear
fi

# Запускаем команду контейнера
exec "$@"
