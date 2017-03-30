#!/usr/bin/env bash

PREVIOUS_DIR=`pwd`
CURRENT_DIR=`cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd`
cd ${CURRENT_DIR}
source ./config.sh
echo ">> Stopping docker container ${DOCKER_CONTAINER_ID}..."

docker stop ${DOCKER_CONTAINER_ID} &>/dev/null

echo "<< Docker container stopped."
cd ${PREVIOUS_DIR}
