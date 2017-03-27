#!/usr/bin/env bash

PREVIOUS_DIR=`pwd`
CURRENT_DIR=`cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd`
cd ${CURRENT_DIR}
source ./config.sh

./impl/stop.sh

./impl/clean.sh

./impl/build.sh

./impl/run.sh

cd ${PREVIOUS_DIR}

