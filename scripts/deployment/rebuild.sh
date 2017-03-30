#!/usr/bin/env bash

# Stops existing Lerna container and clean it's base image.
# Runs all build and launch operations to start it again.

PREVIOUS_DIR=`pwd`
CURRENT_DIR=`cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd`
cd ${CURRENT_DIR}
source ./impl/config.sh

./impl/stop.sh

./impl/clean.sh

./impl/build.sh

./impl/run.sh

cd ${PREVIOUS_DIR}

