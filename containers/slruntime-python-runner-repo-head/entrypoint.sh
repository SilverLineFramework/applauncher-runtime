#!/bin/bash
# receives python filename to execute and arguments. e.g: test.py arg1 arg2 arg3

python3=`which python3`
pip=`which pip3`

[ -f requirements.txt ] && ${pip} install -Ur requirements.txt

${python3} -u "$@"