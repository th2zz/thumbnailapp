# change these 2 variables to make sure images built are push to a right place
DOCKER_USERNAME ?= omelet034
IMAGE_REPO_NAME ?= simple-fs
# this variable will fetch the latest commit hash 
GIT_HASH ?= $(shell git log --format="%h" -n 1)
# most recent git commit hash is used as part of the image tag
_BUILD_TAG ?= ${GIT_HASH}
_LATEST_TAG ?= latest
_DOCKERFILE ?= Dockerfile
IMAGE-NAME-HASH-TAGGED ?= ${DOCKER_USERNAME}/${IMAGE_REPO_NAME}:${_BUILD_TAG}
IMAGE-NAME-LATEST-TAGGED ?= ${DOCKER_USERNAME}/${IMAGE_REPO_NAME}:${_LATEST_TAG}
# specify an offcial python image https://hub.docker.com/_/python
PYTHON_BASE_IMAGE ?= python:3.11.0-slim
# specify a python image with poetry pre-installed
POETRY_BASE_IMAGE ?= python-3.11.0-slim-poetry
POETRY_BASE_IMAGE_DOCKERFILE ?= Dockerfile.base
POETRY_BASE_IMAGE_LATEST ?= ${DOCKER_USERNAME}/${POETRY_BASE_IMAGE}:${_LATEST_TAG}

_build:
	docker build -t ${IMAGE-NAME-HASH-TAGGED} -f ${_DOCKERFILE} .
_push:
	docker push ${IMAGE-NAME-HASH-TAGGED}
_pull:
	docker pull ${IMAGE-NAME-HASH-TAGGED}
_run:
	docker run -p 8080:8080 ${IMAGE-NAME-HASH-TAGGED}
_release_latest:
	docker pull ${IMAGE-NAME-HASH-TAGGED}
	docker tag  ${IMAGE-NAME-HASH-TAGGED} ${IMAGE-NAME-LATEST-TAGGED}
	docker push ${IMAGE-NAME-LATEST-TAGGED}
# https://python-poetry.org/docs/
install_poetry:
	curl -sSL https://install.python-poetry.org | python3 - --git https://github.com/python-poetry/poetry.git@master && source ~/.bashrc
# poetry dump dependencies as requirements.txt
dump_dep:
	poetry export --without-hashes --format=requirements.txt > requirements.txt
update_dep:
	poetry update
build_dep:
	poetry install
# build the builder base image and push it
prepare_base_image:
	docker build --build-arg OFFICIAL_PYTHON_IMAGE=${PYTHON_BASE_IMAGE} \
					-t ${POETRY_BASE_IMAGE_LATEST} -f ${POETRY_BASE_IMAGE_DOCKERFILE} .
	docker push ${POETRY_BASE_IMAGE_LATEST}
build_all:
	$(MAKE) build_dev
	$(MAKE) build_test
	$(MAKE) build_prod
push_all:
	$(MAKE) push_dev
	$(MAKE) push_test
	$(MAKE) push_prod
# this target is for testing this make file: it builds all versions of images, push them to registry, mark the prod one as latest and push it again
release_all:
	$(MAKE) build_all
	$(MAKE) push_all
	$(MAKE) release_latest_prod
# dynammic target: 
# for example, build_dev will build an image with tag dev-<githash> using dockerfile Dockerfile.dev
build_%:
	$(MAKE) _build \
			-e _BUILD_TAG="$*-${GIT_HASH}" \
			-e _DOCKERFILE="Dockerfile.$*"
push_%:
	$(MAKE) _push \
			-e _BUILD_TAG="$*-${GIT_HASH}"
# pull latest dev / test / prod according to most recent git hash
pull_%:
	$(MAKE) _pull \
			-e _BUILD_TAG="$*-${GIT_HASH}"
# run the image with latest tag
run_latest:
	$(MAKE) _run \
			-e _BUILD_TAG=${_LATEST_TAG}
# run latest prod
run:
	$(MAKE) run_prod \
			-e _BUILD_TAG="$*-${GIT_HASH}"
# run latest dev / prod / test image
run_%:
	$(MAKE) _run \
			-e _BUILD_TAG="$*-${GIT_HASH}"
# try to pull the image with most recent commit hash tag, tag it as latest and push it 
release_latest_%:
	$(MAKE) _release_latest \
			-e _BUILD_TAG="$*-${GIT_HASH}"
# build the specific version and push it with git hash as tag, finally pull & tag as latest and push again
release_%:
	$(MAKE) build_$*
	$(MAKE) push_$*
	$(MAKE) release_latest_$*
# run test locally without (no container)
test_local:
	poetry run pytest tests/ --cov=app --cov-report=term-missing
# start the server locally (no container)
run_local:
	poetry run uvicorn --workers 1 --host 0.0.0.0 --port 8080 app.main:app
# build test image locally with git hash tag, run the container afterward
test:
	$(MAKE) build_test
	$(MAKE) run_test
.PHONY: build_% push_% release_% init