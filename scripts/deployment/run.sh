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
# --sig-proxy=false         - do not proxy console commands (Ctrl+C) inside
# -d                        - detach right after container was started
# --publish <host>:<docker> - publish exposed <docker> port at <host> one
# --name <name>             - docker container uid
# --volume <local>:<docker> - mount <local> directory into containers <docker> directory
docker run \
       --sig-proxy=false \
       --publish 80:3000 \
       --name ${DOCKER_CONTAINER_ID} \
       --volume ${PROJECT_DIR}:/lerna \
       ${DOCKER_IMAGE_ID}
