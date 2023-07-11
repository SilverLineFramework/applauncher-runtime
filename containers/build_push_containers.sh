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

for folder in *; do
    if [ -d "$folder" ]; then
      [ -f "$folder/VERSION" ] && VERSION=$(cat "$folder/VERSION")
      IMG_TAG=${VERSION:-latest}
      IMG_NAME="$folder"

      cd $SCRIPT_DIR/$folder

      echo "building: "$IMG_NAME:$IMG_TAG

      # create a multiarch build
      #docker buildx create --use
      #docker buildx build --platform=linux/arm64/v8,linux/amd64 . -t $DOCKER_USER/$IMG_NAME
      docker build . -t $DOCKER_USER/$IMG_NAME
      docker tag $DOCKER_USER/$IMG_NAME:latest $DOCKER_USER/$IMG_NAME:$IMG_TAG

      if [[ $PUSH_IMG = "true" ]]; then
        echo $DOCKER_PASSWD | docker login --username $DOCKER_USER --password-stdin
        docker push $DOCKER_USER/$IMG_NAME
        docker push $DOCKER_USER/$IMG_NAME:$IMG_TAG
        echo "pushed: "$DOCKER_USER/$IMG_NAME:$IMG_TAG
      fi
    fi
done
