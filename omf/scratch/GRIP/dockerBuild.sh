#!/bin/sh
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $SCRIPT_DIR/../../..
cp omf/scratch/GRIP/grip.Dockerfile .
cp omf/scratch/GRIP/grip.py omf/
# Build and restart container.
docker build . -f grip.Dockerfile -t grip
#docker stop grip_run
#docker rm grip_run
#docker run -d -p 5100:5100 --name grip_run grip
#open http://localhost:5100
# Cleanup.
rm omf/grip.py
rm grip.Dockerfile