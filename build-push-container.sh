#!/bin/bash
# NOTE: github workflow will create the image automatically on a release
# use this script only if you want to manually build and push the container
# usage: ./build-push-container.sh [-b: build-only]

# check if -b (build-only was passed)
while getopts b flag
do
    case "${flag}" in
        b) push="";;
    esac
done
PUSH_IMG=${push:-"--push"} # by default will push image

IMG_NAME="applauncher-runtime"

# update version as needed
VERSION=v1.2.0
IMG_TAG=${VERSION:-latest}

# load secrets
export $(grep -v '^#' ./containers/.secrets.env | xargs)

docker buildx rm slctnrbuilder 2>/dev/null

# stop on first error
set -e

docker buildx create --name slctnrbuilder --use --bootstrap

echo $DOCKER_PASSWD | docker login --username $DOCKER_USER --password-stdin

docker buildx build . --no-cache $PUSH_IMG --platform linux/amd64,linux/arm64/v8  -t $DOCKER_USER/$IMG_NAME:latest -t $DOCKER_USER/$IMG_NAME:$IMG_TAG 

docker buildx rm slctnrbuilder
