#!/bin/bash
# update VERSION to lastest arena-py from pip

LATEST=$(pip index versions arena-py 2>/dev/null | grep ^arena-py | cut -f2 -d"(" | tr -d ")")

echo "v$LATEST"
echo "$LATEST" > VERSION