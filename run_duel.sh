#!/bin/bash -e

if [[ $# -lt 4 ]]; then
    echo "Run a duel to completion"
    echo "Usage: $0 <namespace> <image_1> <image_2> <environment> <output_file>"
    exit 1
fi

NAMESPACE="$1"

# Make sure all previous containers are down
docker-compose --project-name "$NAMESPACE" --file run_duel/docker-compose.yml down

# Start duel runner
DUEL_NAMESPACE="$NAMESPACE" \
DUEL_IMAGE_1="$2" \
DUEL_IMAGE_2="$3" \
DUEL_ENVIRONMENT="$4" \
DUEL_OUTPUT_FILE="$5" \
GS_BUCKET_NAME="$GS_BUCKET_NAME" \
    docker-compose --project-name "$NAMESPACE" --file run_duel/docker-compose.yml \
    up run_duel

docker-compose --project-name "$NAMESPACE" --file run_duel/docker-compose.yml down