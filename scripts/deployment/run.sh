#!/usr/bin/env bash

# Importing names from data.sh
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd ${CURRENT_DIR}
source ./data/config.sh

# Remove old and exited containers
docker ps -a | grep 'Exited' | awk '{print $1}' | xargs --no-run-if-empty docker rm -f

echo "Checking if ${DOCKER_ID} is already running..."
if [ `docker inspect -f {{.State.Running}} ${DOCKER_ID}` ]; then
    echo "Server is already running"
    exit 0
fi

docker run \
       --name ${DOCKER_ID} \
       --net="host" \
       --volume ${PROJECT_DIR}:/lerna \
       ${CONTAINER_ID}
