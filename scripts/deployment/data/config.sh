#!/usr/bin/env bash

# Docker running process name
DOCKER_ID=lerna_web

# Docker image name
CONTAINER_ID=lerna/web

# Script directory (/scripts/deployment/data)
CONFIG_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Project directory
PROJECT_DIR=${CONFIG_DIR}/../../../
PROJECT_DIR=`readlink -f ${PROJECT_DIR}` # resolving path
