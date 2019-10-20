#!/bin/bash -e

# This file will run duel to completion
# It receives its parameters via environment variables:

# Select a new unique namespace
NAMESPACE=$(openssl rand -hex 8)

# Start duel runner
DUEL_NAMESPACE="$NAMESPACE" \
DUEL_IMAGE_1="$DUEL_IMAGE_1" \
DUEL_IMAGE_2="$DUEL_IMAGE_2" \
DUEL_ENVIRONMENT="$DUEL_ENVIRONMENT" \
DUEL_OUTPUT_FILE="$DUEL_OUTPUT_FILE" \
    docker-compose --project-name "$NAMESPACE" --file run_duel/docker-compose.yml \
    up run_duel || true

docker-compose --project-name "$NAMESPACE" --file run_duel/docker-compose.yml logs

# Turn make sure all containers are down
docker-compose --project-name "$NAMESPACE" --file run_duel/docker-compose.yml down