#!/bin/bash
# usage ./start-runtime1 [target-config]
# where target-config specifies the config to be used (e.g. arenaxr or dev-1); default is arenaxr

TARGET="${1:-$arenaxr}"
screen -L -Logfile /home/wiselab/silverline/applauncher-runtime/slruntime.log -S slruntime1 -dm bash -c "make config/${TARGET}"
