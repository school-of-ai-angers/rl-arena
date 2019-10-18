#!/bin/bash -e

# Postgres
docker-compose up --build -d db
sleep 10

# Main Django app
docker-compose up --build -d web