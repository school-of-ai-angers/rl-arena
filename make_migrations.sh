#!/bin/bash -e

DB_DIR="$PWD/data/make_migrations"
NAMESPACE=rl_arena_make_migrations

echo === Build ===
docker build --quiet --tag rl-arena .

echo === Prepare database ===
sudo rm -r "$DB_DIR" || true
POSTGRES_DIR=make_migrations docker-compose --project-name "$NAMESPACE" up -d db
sleep 30

echo === Run previous migration to bring DB up to date ===
docker-compose --project-name "$NAMESPACE" run web "python manage.py migrate" || true

echo === Create new migration ===
docker-compose --project-name "$NAMESPACE" run \
    --volume "$PWD/web/migrations":/app/web/migrations web \
    "python manage.py makemigrations" || true
sudo chown -R "$(id -u):$(id -g)" web/migrations

echo === Tear down ===
docker-compose --project-name "$NAMESPACE" down