#!/bin/bash -e

DB_DIR="$PWD/data/make_migrations"
NAMESPACE=rl_arena_make_migrations

echo === Build ===
docker build --quiet --tag rl-arena .

echo === Prepare database ===
sudo rm -r "$DB_DIR" || true
POSTGRES_DIR=make_migrations docker-compose --project-name "$NAMESPACE" up -d db
sleep 15

echo === Run previous migration to bring DB up to date ===
docker-compose --project-name "$NAMESPACE" run --rm -T migrate || true

echo === Create new migration ===
docker-compose --project-name "$NAMESPACE" run --rm make_migrations || true
sudo chown -R "$(id -u):$(id -g)" core/migrations

echo === Tear down ===
docker-compose --project-name "$NAMESPACE" down