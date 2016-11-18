#!/usr/bin/env bash

# Importing names
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd ${CURRENT_DIR}
source ./data/config.sh

# Remove old containers
docker ps -a | grep 'Exited' | awk '{print $1}' | xargs --no-run-if-empty docker rm -f
# Remove unnamed and intermediate images
docker images | grep "<none>" | awk '{print $3}' | xargs --no-run-if-empty docker rmi
# Remove previous lerna/web images
docker images | grep "${DOCKER_IMAGE_ID}" | awk '{print $3}' | xargs --no-run-if-empty docker rmi
# Clean build files
rm -rf ${PROJECT_DIR}/build/*
