#!/usr/bin/env bash

PREVIOUS_DIR=`pwd`
CURRENT_DIR=`cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd`
cd ${CURRENT_DIR}
source ./impl/config.sh

./impl/stop.sh

if docker images | grep -q ${DOCKER_IMAGE_ID}
then
   echo "using existing image ${DOCKER_IMAGE_ID}";
else
   ./impl/build.sh
fi

./impl/run.sh

cd ${PREVIOUS_DIR}
