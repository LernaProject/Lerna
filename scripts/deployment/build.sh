#!/usr/bin/env bash

# Importing names from data.sh
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd ${CURRENT_DIR}
source ./data/config.sh

# Cleaning all old and intermediate data before build
./clean.sh

# requirements.txt copy in data directory to use it in build
cp ${PROJECT_DIR}/requirements.txt ./data/requirements.txt.tmp

# Build image from ./data/ directory
# --no-cache - do not use cached intermediate containers
# --force-rm - remove all intermediate containers after build
# -t <name>  - container name
docker build --no-cache --force-rm -t ${DOCKER_IMAGE_ID} ./data/

# Removing temporary requirements.txt copy
rm ./data/requirements.txt.tmp
