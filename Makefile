DOCKER_USERNAME ?= omelet034
IMAGE_REPO_NAME ?= thumbnail-app
GIT_HASH ?= $(shell git log --format="%h" -n 1)
_BUILD_TAG ?= ${GIT_HASH}
_LATEST_TAG ?= latest
_DOCKERFILE ?= Dockerfile
IMAGE-NAME-HASH-TAGGED ?= ${DOCKER_USERNAME}/${IMAGE_REPO_NAME}:${_BUILD_TAG}
IMAGE-NAME-LATEST-TAGGED ?= ${DOCKER_USERNAME}/${IMAGE_REPO_NAME}:${_LATEST_TAG}
PYTHON_BASE_IMAGE ?= python:3.11.0-slim
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
dump_dep:
	poetry export --without-hashes --format=requirements.txt > requirements.txt
update_dep:
	poetry update
build_dep:
	poetry install
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
release_all:
	$(MAKE) build_all
	$(MAKE) push_all
	$(MAKE) release_latest_prod
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
# run latest prod
run_latest:
	$(MAKE) _run \
			-e _BUILD_TAG=${_LATEST_TAG}
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
# run test locally without container
test_local:
	poetry run pytest tests/ --cov=app --cov-report=term-missing
# build test image locally with git hash tag, run the container afterward
test:
	$(MAKE) build_test
	$(MAKE) run_test
.PHONY: build_% push_% release_% init