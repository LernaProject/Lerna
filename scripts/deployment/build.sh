#!/usr/bin/env bash

# Importing names from data.sh
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd ${CURRENT_DIR}
source ./data/config.sh

./clean.sh

# Build container
# -t lerna/web - container name
# --no-cache   - do not use cached intermediate containers
# --force-rm         - remove all intermediate containers after build
docker build --no-cache --force-rm -t ${CONTAINER_ID} ./data/
