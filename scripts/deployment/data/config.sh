#!/usr/bin/env bash

DOCKER_CONTAINER_ID=lerna_web
DOCKER_IMAGE_ID=lerna/web

# Inside container gUnicorn will use 3020 port, nginx - 3000 (see Dockerfile and docker_run.sh)

# Script directory (/scripts/deployment/data)
CONFIG_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Project directory
PROJECT_DIR=${CONFIG_DIR}/../../../
PROJECT_DIR=`readlink -f ${PROJECT_DIR}` # resolving path
