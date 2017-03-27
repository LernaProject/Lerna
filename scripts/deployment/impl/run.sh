#!/usr/bin/env bash

PREVIOUS_DIR=`pwd`
CURRENT_DIR=`cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd`
cd ${CURRENT_DIR}
source ./config.sh
echo ">> Launching docker container ${DOCKER_CONTAINER_ID} based on ${DOCKER_IMAGE_ID} image..."

echo "- remove previous ${DOCKER_CONTAINER_ID} container"
docker ps -a | grep ${DOCKER_CONTAINER_ID} | awk '{print $1}' | xargs --no-run-if-empty docker rm -f

echo "- launch new container"
# run docker container from image ${DOCKER_IMAGE_ID}
# -d                        - detach right after container was started
# --name <name>             - docker container uid
# --net="host"              - do not containerise networking
# --sig-proxy=false         - do not proxy console commands (Ctrl+C) inside
# --volume <local>:<docker> - mount <local> directory into containers <docker> directory
docker run \
       -d \
       --name ${DOCKER_CONTAINER_ID} \
       --net="host" \
       --volume ${PROJECT_DIR}:/lerna \
       ${DOCKER_IMAGE_ID}

echo "<< Docker container launched."
cd ${PREVIOUS_DIR}
