#!/bin/bash
if (( $# != 1 )); then
    >&2 echo "Illegal number of parameters. Expected 2, found #$"
fi

CHANNEL_MAP_NAME=$1

cd /dunedaq/run/dunedaq-area
source quick_env.sh
cd ../justintime
pip install -e .
CMD="python -m justintime.app /data ${CHANNEL_MAP_NAME}"
echo ${CMD}
${CMD}
