#!/usr/bin/env bash

# $ docker run --rm --name grip_run -p 5100:5100 grip
# $ docker stop grip_run
# $ docker rm grip_run

cwd="$(pwd)"
cd "$(dirname "${BASH_SOURCE[0]}")"
build_context="$(pwd)"/../../..
docker build -f grip.Dockerfile -t grip "$build_context"
cd "$cwd"