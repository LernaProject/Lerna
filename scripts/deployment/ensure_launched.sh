#!/usr/bin/env bash

PREVIOUS_DIR=`pwd`
CURRENT_DIR=`cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd`
cd ${CURRENT_DIR}
source ./impl/config.sh

DOCKER_STATE=`docker inspect -f {{.State.Running}} ${DOCKER_CONTAINER_ID} 2> /dev/null`
if [[ ${DOCKER_STATE} == *"true"* ]]; then
    exit 0
fi

./restart.sh

cd ${PREVIOUS_DIR}
