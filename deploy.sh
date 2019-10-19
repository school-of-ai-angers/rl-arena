#!/bin/bash -e

# Build
docker build -q -t rl-arena .

# Postgres
PS_BEFORE=$(docker-compose ps -q db)
docker-compose up -d db
if [[ -z $PS_BEFORE ]]; then
    echo "Wait for DB"
    sleep 10
fi

# Migrate DB
docker-compose run web "python manage.py makemigrations && python manage.py migrate"

# Main Django app
docker-compose up web