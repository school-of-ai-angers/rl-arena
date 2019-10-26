#!/bin/bash -e

echo === Build ===
docker build -q -t rl-arena .

echo === Postgres ===
PS_BEFORE=$(docker-compose ps -q db)
docker-compose up -d db
if [[ -z $PS_BEFORE ]]; then
    echo "Wait for DB"
    sleep 15
fi

echo === Migrate DB ===
docker-compose run --rm -T migrate

echo === Main Django app ===
docker-compose up -d builder smoke_tester tournament_manager duel_runner
docker-compose run --publish 8000:8000 \
    --volume "$PWD/builder:/app/builder:ro" \
    --volume "$PWD/core:/app/core:ro" \
    --volume "$PWD/web:/app/web:ro" \
    --rm -T web