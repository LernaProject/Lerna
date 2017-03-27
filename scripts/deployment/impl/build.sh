#!/usr/bin/env bash

PREVIOUS_DIR=`pwd`
CURRENT_DIR=`cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd`
cd ${CURRENT_DIR}
source ./config.sh
echo ">> Building docker image ${DOCKER_IMAGE_ID}..."

echo "- copy temporary files"
cp ${PROJECT_DIR}/requirements.txt ${DOCKER_BUILD_DIR}/requirements.txt.tmp

echo "- call docker build"
# Build image from ./data/ directory
# --no-cache - do not use cached intermediate images
# --force-rm - remove all intermediate containers after build
# -t <name>  - image name
docker build --no-cache --force-rm -t ${DOCKER_IMAGE_ID} ${DOCKER_BUILD_DIR}/

echo "- remove temporary files"
rm ${DOCKER_BUILD_DIR}/requirements.txt.tmp

echo "<< Docker image building done."
cd ${PREVIOUS_DIR}
