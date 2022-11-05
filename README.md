# Intro

This project uses:

- [Poetry](https://python-poetry.org/): for dependency management
- [FastAPI](https://fastapi.tiangolo.com/): as web framework
- [uvicorn](https://www.uvicorn.org/): as server program
- [pytest-bdd](https://pypi.org/project/pytest-bdd/): for integration test
- [pytest](https://pypi.org/project/pytest/): for unit testing
- [pytest-cov](https://pypi.org/project/pytest-cov/): for coverage report
- [pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks) for pre-commit code check
- [black](https://github.com/psf/black) for pre-commit code formatting

# Quick Start

## Dependencies Management:

- install all dependencies
  - ```shell
    make build_dep
    ```
- update all dependencies
  - ```shell
    make update_dep
    ```
- dump all dependencies as requirements.txt
  - ```shell
    make dump_dep
    ```

## Build Docker image:

- build dev image
  - ```shell
    make build_dev
    ```
- build test image (used for running unit test in container)
  - ```shell
    make build_test
    ```
- build prod image
  - ```shell
    make build_prod
    ```

## Run application:

- locally
  - ```shell
    poetry run uvicorn --workers 1 --host 0.0.0.0 --port 8080 app.main:app
    ```
- in container

  - ```shell
    make run_prod  # run latest prod level container
    ```

## Run tests

- locally
  - ```shell
    make test_local
    ```
- in container

  - ```shell
    make test
    ```
