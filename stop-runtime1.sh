#!/bin/bash

screen -X -S slruntime1 quit 
#screen -ls | grep '(Detached)' | awk '{print $1}' | xargs -I % -t screen -X -S % quit
(docker kill `docker ps | grep slruntime-python-runner | cut -d" " -f1` 2>&1) > /dev/null

