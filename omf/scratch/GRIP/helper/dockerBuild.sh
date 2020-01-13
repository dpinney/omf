#!/usr/bin/env bash

# $ docker run --rm --name omf_grip_run -p 5100:5100 omf_grip
# $ docker stop omf_grip_run
# $ docker rm omf_grip_run

cwd="$(pwd)"
cd "$(dirname "${BASH_SOURCE[0]}")"
build_context="$(pwd)"/../../../..
docker build -f ../grip.Dockerfile -t omf_grip "$build_context"
cd "$cwd"
