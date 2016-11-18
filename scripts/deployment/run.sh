#!/usr/bin/env bash

# Importing names
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd ${CURRENT_DIR}
source ./data/config.sh

# Remove old containers
docker ps -a | grep 'Exited' | awk '{print $1}' | xargs --no-run-if-empty docker rm -f

echo "Checking if ${DOCKER_CONTAINER_ID} is already running..."
if [ `docker inspect -f {{.State.Running}} ${DOCKER_CONTAINER_ID}` ]; then
    echo "Server is already running"
    exit 0
fi

# run docker container from image ${DOCKER_IMAGE_ID}
# --name <name>             - docker container uid
# --net="host"              - allow docker image use local resources
# --volume <local>:<docker> - mount <local> directory into containers <docker> directory
docker run \
       --name ${DOCKER_CONTAINER_ID} \
       --net="host" \
       --volume ${PROJECT_DIR}:/lerna \
       ${DOCKER_IMAGE_ID}
