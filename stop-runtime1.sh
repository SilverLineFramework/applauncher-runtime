#!/bin/bash

# sending 'Q' to runtime will request it to exit gracefully (cleanup containers)
screen -S slruntime1 -X stuff 'Q'`echo -ne '\015'` 
attempt=1
while screen -list | grep -q slruntime1
do
	if [ attempt -eq 1 ]; then
		echo "Waiting for runtime to exit gracefully"
	fi
	if [ $attempt -gt 20 ]; then
        echo "Runtime did not exit after $max_attempts attempts, forcefully stopping it."
        screen -X -S slruntime1 quit
        break
    fi
    attempt=$((attempt + 1))    
    sleep 1
done
# still try to kill runner containers in case exit failed to cleanup correctly
echo "This many runners still alive (should be zero; will kill them if not): "`docker ps | grep slruntime-python-runner | wc -l`
(docker kill `docker ps | grep slruntime-python-runner | cut -d" " -f1` 2>&1) > /dev/null 

