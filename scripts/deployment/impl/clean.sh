#!/usr/bin/env bash

PREVIOUS_DIR=`pwd`
CURRENT_DIR=`cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd`
cd ${CURRENT_DIR}
source ./config.sh
echo ">> Cleaning old docker images..."

echo "- remove previous ${DOCKER_CONTAINER_ID} container"
docker ps -a | grep ${DOCKER_CONTAINER_ID} | awk '{print $1}' | xargs --no-run-if-empty docker rm -f
echo "- remove nameless images"
docker images | grep "<none>" | awk '{print $3}' | xargs --no-run-if-empty docker rmi
echo "- remove previous ${DOCKER_IMAGE_ID} image"
docker images | grep "${DOCKER_IMAGE_ID}" | awk '{print $3}' | xargs --no-run-if-empty docker rmi

echo "<< Docker images cleanup done."
cd ${PREVIOUS_DIR}
