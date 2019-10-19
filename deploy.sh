#!/bin/bash -e

echo === Build ===
docker build -q -t rl-arena .

echo === Postgres ===
docker-compose up -d db

echo === Migrate DB ===
docker-compose run web "python manage.py migrate"

echo === Main Django app ===
docker-compose up -d web