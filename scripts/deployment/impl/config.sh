SCRIPT_DIR=`cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd`

DOCKER_CONTAINER_ID=lerna_web
DOCKER_IMAGE_ID=lerna/web
DOCKER_BUILD_DIR=${SCRIPT_DIR}/../data/

PROJECT_DIR=${SCRIPT_DIR}/../../../
PROJECT_DIR=`readlink -f ${PROJECT_DIR}` # resolving path
