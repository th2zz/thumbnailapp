# Table of contents

- [Intro](#intro)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
  - [Usage Example](#usage-example)
    - [docker compose](#docker-compose)
    - [Create a new thumbnail](#create-a-new-thumbnail)
    - [Get a thumbnail file by task id](#get-a-thumbnail-file-by-task-id)
    - [Get thumbnail info json by task id](#get-thumbnail-info-json-by-task-id)
  - [Dependencies Management](#dependencies-management)
  - [Build Docker image](#build-docker-image)
  - [Run Application Server Individually](#run-application-server-individually)
  - [Run Celery Worker Individually](#run-celery-worker-individually)
  - [Run Tests](#run-tests)
- [Things to Notice / Improve](#things-to-notice---improve)

# Intro

Name: Tinghe Zhang Email: tzhang329@gmail.com
This project uses:

- [mongodb](https://www.mongodb.com/) for storing auxillary tasks info and thumbnail base64 data
- [pillow](https://pillow.readthedocs.io/) for image resize
- [celery](https://github.com/celery/celery): as task queue framework
- [redis](https://redis.io/) as celery broker
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
                                                       ┌──────────────────────────┐
                                                       │                          │
                                                       │     redis(broker)        │
                                                       │                          │
                                                       └──────────────────────────┘
                                                            ▲
                                                            │
                                                            │
                                                        ┌───▼──────────────────┐
 POST /thumbnail  Content-Type: application/json        │                      │
body: {"source_image_url": <an image url>}              │    celery            │◄────────────┐
response: {"task_id": <celery task id>}                 │                      │             │
                                                        └──────────────────────┘             │
                   ┌──────────────────────────┐            ▲                                 │
────────────────►  │                          │            │                                 │
                   │    FastAPI backend       │            │                                 ▼
────────────────►  │                          ├────────────┘                           ┌───────────────┐
                   └──────────────────────────┘                                        │               │
GET                                                                                    │ celery worker │
  /thumbnail?task_id=<task_id>      get a json containing thumbnail base64 data        │               │
  /thumbnail/file?task_id=<task_id>  get thumbnail file bytes                          │               │
                                                                                       └───────────────┘

                                            resize_image_task

                                            1. download image from url [This is the only part that write to disk]
                                            2. compute sha256 of the image
                                            3. if there is a document with the same
                                               hash, create a new entry in mongo tasks collection
                                               mark as complete and return to avoid recomputation
                                            4. if this is a brand new image, resize it and
                                               store {"sha256hex": <sha256>, "base64_thumbnail":
                                               <base64 thumbnail data>, "last_modify_time": <timestamp>}
                                               in thumbnails collection
```

endpoints

- /docs
  - GET automatically generated OpenAPI docs
- /health
  - GET health check
- /thumbnail
  - POST create a thumbnail from an image URL, submitted celery task_id is included in response for client to use later
- /thumbnail?task_id=
  - GET Get thumbnail info json by task_id, thumbnail data is base64 encoded
- /thumbnail/file?task_id=
  - GET thumbnail file bytes by task id

# Quick Start

## Usage Example

### docker compose

```
docker-compose up
```

### Create a new thumbnail

Create a new thumbnail, response will have a generated celery task id, you can use it to look up status or fetch result

```shell
root@LAPTOP-4PFU6A8D:~/thumbnailapp# curl -X POST http://localhost:8080/thumbnail -H "Content-Type: application/json" -d '{"source_image_url": "https://pyxis.nymag.com/v1/imgs/55b/438/d732205198d1fc4b0aafc8bb302e4e68c2-john-wick.rsquare.w330.jpg"}'
{"task_id":"6381c22b-2b21-498e-bca7-af9cc864c1eb"}
```

### Get a thumbnail file by task id

```
root@LAPTOP-4PFU6A8D:~/thumbnailapp# curl http://localhost:8080/thumbnail/file?task_id=6381c22b-2b21-498e-bca7-af9cc864c1eb > abc.jpeg
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  3013    0  3013    0     0   588k      0 --:--:-- --:--:-- --:--:--  588k
```

### Get thumbnail info json by task id

reponse is a json containing thumbnail bytes encoded in base64 string format

```
root@LAPTOP-4PFU6A8D:~# curl http://localhost:8080/thumbnail?task_id=15bda50a-0f9a-4a3b-8449-cc7c9bc0452e
{"message":"ok","task_id":"15bda50a-0f9a-4a3b-8449-cc7c9bc0452e","status":"SUCCESS","base64_thumbnail_data":"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"}
```

## Dependencies Management

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

## Build Docker image

- build dev image for the server
  - ```shell
    make build_dev
    ```
- build test image (used for running unit test in a dedicated container)
  - ```shell
    make build_test
    ```
- build prod image for the server
  - ```shell
    make build_prod
    ```
- build the worker image
  - ```shell
    make prepare_worker_image
    ```

## Run Application Server Individually

- locally (no container)
  - ```shell
    make run_local
    ```
- in container
  - ```shell
    make run_prod  # run latest prod level image
    ```

## Run Celery Worker Individually

- locally
  - ```shell
    poetry celery -A app.worker.celery worker --loglevel=info
    ```
- in container
  - ```shell
    make run_worker  # run latest worker image
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

# Things to Notice / Improve

- RESTful API should be versioned in production setting for better evolvability and backward compatibility
- since we are downloading images to disk in worker. If we are using kubernetes, a separate cron job / sidecar will be needed to clean up downloaded images regularly otherwise the volume will blow up
- Authentication is not implemented
- prometheus /metrics endpoint is exposed
  - a couple of basic metrics are included such as http_requests_total, http_request_size_bytes, http_request_duration_seconds, disk_usage ... etc.
- I used redis as broker for **simplicity**
  - expire time can be set to automatically clean up old keys / data
  - redis is a single point of failure, for a large cluster with HA set-up and better performance, redis cluster should be used
- I used mongodb for storing some auxiliary tasks information, image sha256, image thumbnail base64 data, so it basically becomes a custom result backend, therefore I disabled native result backend from celery
  - mongo is a single point of failure, for a large cluster with HA set-up and better performance, mongoDB atlas or other similar document store / kv store can be used
  - [TTL indexes](https://www.mongodb.com/docs/manual/core/index-ttl/) can be created to automatically clean up documents in mongodb collection
- Unit Tests / Integration Tests should be improved
  - To improve test coverage,
    - a lot of monkeypatch will be needed because celery and mongo is used. Since I have limited time, I only implemented the most important one.
    - More edge cases tests should be included: e.g. bad requests, invalid image url from response body
      - for the GET thumbnail, edge cases like bad task_id should be included
  - the test image seems to have some bug and within the container it will have 1 test partially failed compared to running locally (all passed)
    - pytest-celery related fixtures and "broker_url='memory://" seems to not configured correctly. In container setting, it is still trying to connect to redis.
