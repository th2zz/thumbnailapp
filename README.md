# Intro

This project uses:

- [Poetry](https://python-poetry.org/): for dependency management
- [FastAPI](https://fastapi.tiangolo.com/): as web framework
- [uvicorn](https://www.uvicorn.org/): as server program
- [pytest](https://pypi.org/project/pytest/): for unit testing
- [pytest-cov](https://pypi.org/project/pytest-cov/): for coverage report
- [pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks) for pre-commit code check
- [black](https://github.com/psf/black) for pre-commit code formatting
- [prometheus_client](https://github.com/prometheus/client_python) and [prometheus-fastapi-instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator) for basic metrics

# Architecture

```
                                                        On POST file
                                                        BackgroundTasks: Read file stream chunk by chunk
                                                                         and write to local path
  POST /files/     ┌──────────────────────────┐            ▲             (Thread pool based)
────────────────►  │                          │            │           │
                   │    FastAPI backend       │            │           │
────────────────►  │                          ├────────────┘           │
  GET /files/<name>└──────────────────────────┘                        │
                                                                       │
                                                                       │
                                                                       ▼
                                                   ┌─────────────────────────────────┐
                                                   │                                 │
                                                   │                                 │
                                                   │   CephFileSystem (shared)       │
                                                   │   managed by Rook Ceph Operator │
                                                   │                                 │
                                                   └─────────────────────────────────┘
```

# Caveat

- authentication is not implemented

# Quick Start

## Dependencies Management:

This project use poetry for dependencies management.

- install poetry locally
  - refer to [offcial doc](https://python-poetry.org/docs/) or use the following command
    ```shell
    make install_poetry
    ```
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
- build test image (used for running unit test in a dedicated container)
  - ```shell
    make build_test
    ```
- build prod image
  - ```shell
    make build_prod
    ```

## Run Application:

- locally (no container)
  - ```shell
    make run_local
    ```
- in container
  - ```shell
    make run_prod  # run latest prod level image
    ```

## Run Tests

- locally (no container)
  - ```shell
    make test_local
    ```
- in container (build a test image first and then run it)
  - ```shell
    make test
    ```
