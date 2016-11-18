#!/usr/bin/env bash

# Importing names from data.sh
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd ${CURRENT_DIR}
source ./data/config.sh

# Remove old and exited containers
docker ps -a | grep 'Exited' | awk '{print $1}' | xargs --no-run-if-empty docker rm -f
# Remove unnamed and intermediate images
docker images | grep "<none>" | awk '{print $3}' | xargs docker rmi
# Remove previous docker container
docker rmi ${CONTAINER_ID}