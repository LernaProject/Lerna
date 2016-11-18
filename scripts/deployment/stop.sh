#!/usr/bin/env bash

# Importing names
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd ${CURRENT_DIR}
source ./data/config.sh

echo "Stopping ${DOCKER_CONTAINER_ID} if exists..."
docker stop ${DOCKER_CONTAINER_ID}
