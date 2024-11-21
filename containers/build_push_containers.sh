#!/bin/bash
# builds containers from Dockerfiles and pushes them to dockerhub.
# usage: ./build-push-container.sh [-b: build-only]

# check if -b (build-only was passed)
while getopts b flag
do
    case "${flag}" in
        b) push="";;
    esac
done
PUSH_IMG=${push:-"--push"} # by default will push image

# load secrets
export $(grep -v '^#' .secrets.env | xargs)

SCRIPT_DIR="${PWD}"

docker buildx rm slctnrbuilder 2>/dev/null

# stop on first error
set -e

docker buildx create --name slctnrbuilder --use --bootstrap


echo $DOCKER_PASSWD | docker login --username $DOCKER_USER --password-stdin

# each subfolder is a docker image to be created
for folder in */; do
    folder=${folder%/} # remove trailing /

    cd $SCRIPT_DIR/$folder
    VERSION="$(./update_version.sh)"
    IMG_TAG=${VERSION:-latest}
    IMG_NAME="$folder"

    echo "building: "$IMG_NAME:$IMG_TAG
    docker buildx build . --no-cache $PUSH_IMG --platform linux/amd64,linux/arm64/v8  -t $DOCKER_USER/$IMG_NAME:latest -t $DOCKER_USER/$IMG_NAME:$IMG_TAG    
    cd $SCRIPT_DIR
done

docker buildx rm slctnrbuilder
