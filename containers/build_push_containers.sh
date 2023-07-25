#!/bin/bash
# builds containers from Dockerfiles and pushes them to dockerhub.
# usage: ./build-push-container.sh [-b: build-only]

# check if -b (build-only was passed)
while getopts b flag
do
    case "${flag}" in
        b) push="false";;
    esac
done
PUSH_IMG=${push:-"true"} # by default will push image

# stop on first error
set -e

# load secrets
export $(grep -v '^#' .secrets.env | xargs)

SCRIPT_DIR="${PWD}"

# each subfolder is a docker image to be created
for folder in */; do
    folder=${folder%/} # remove trailing /
    [ -f "$folder/VERSION" ] && VERSION=$(cat "$folder/VERSION")
    IMG_TAG=${VERSION:-latest}
    IMG_NAME="$folder"

    cd $SCRIPT_DIR/$folder

    echo "building: "$IMG_NAME:$IMG_TAG

    docker build . -t $DOCKER_USER/$IMG_NAME --no-cache
    docker tag $DOCKER_USER/$IMG_NAME:latest $DOCKER_USER/$IMG_NAME:$IMG_TAG

    if [[ $PUSH_IMG = "true" ]]; then
      echo $DOCKER_PASSWD | docker login --username $DOCKER_USER --password-stdin
      docker push $DOCKER_USER/$IMG_NAME
      docker push $DOCKER_USER/$IMG_NAME:$IMG_TAG
      echo "pushed: "$DOCKER_USER/$IMG_NAME:$IMG_TAG
    fi
    cd $SCRIPT_DIR
done
