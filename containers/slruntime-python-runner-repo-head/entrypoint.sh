#!/bin/bash
# receives python filename to execute and arguments. e.g: test.py arg1 arg2 arg3

python=`which python3`
pip=`which pip3`

cd /usr/src/app
ls /usr/src/app

[ -f requirements.txt ] && ${pip} install -Ur requirements.txt

${python} -u "$@"