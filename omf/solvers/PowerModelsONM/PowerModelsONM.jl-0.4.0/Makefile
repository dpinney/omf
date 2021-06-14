.PHONY: test build build-docker test-docker

TAG = latest

# build docker container
build-docker:
	docker build -f Dockerfile -t PowerModelsONM:dev ${CURDIR}

# build binary
build:
	julia -q --project=. -e 'using PackageCompiler; create_app(".", "build"; force=true);'

# TODO: build unit tests, add network to docker container
test-docker:
	docker run PowerModelsONM:dev --verbose -n -o
