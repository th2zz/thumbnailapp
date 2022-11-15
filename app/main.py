# coding=utf-8
import logging.config
import os
import shutil

import validators
from celery.result import AsyncResult
from fastapi import FastAPI, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from prometheus_client import Gauge
from prometheus_fastapi_instrumentator import Instrumentator

from app.constants import (DEFAULT_READ_BATCH_SIZE, DEFAULT_STORAGE_DIR,
                           MONOGO_DB_NAME, SUPPORTED_IMG_EXTENSIONS,
                           TASKS_COLLECTION_NAME, THUMBNAILS_COLLECTION_NAME)
from app.models import (HealthStatus, ResponseMessage, ThumbnailRequestBody,
                        ThumbnailResponse)
from app.utils import MongoConnector
from app.worker import resize_image_task

CURR_FILE_PATH = os.path.abspath(__file__)
LOGGING_CONF_PATH = os.path.join(os.path.dirname(CURR_FILE_PATH),
                                 'logging.conf')
logging.config.fileConfig(LOGGING_CONF_PATH,
                          disable_existing_loggers=False)
# root level logger
logger = logging.getLogger(__name__)
os.makedirs(DEFAULT_STORAGE_DIR, exist_ok=True)
# This is a unified storage path for both api server and worker
STORAGE_ROOT = os.environ.get("STORAGE_ROOT", DEFAULT_STORAGE_DIR)
FILE_READ_BATCH_SIZE = os.environ.get("FILE_READ_BATCH_SIZE",
                                      DEFAULT_READ_BATCH_SIZE)
app = FastAPI()
disk_used = Gauge(
    "disk_used",
    "Percentage disk used. (The disk that $STORAGE_ROOT is at)",
    labelnames=("disk_used",)
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/")
MONGO_CLIENT = MongoConnector(MONGO_URL, MONOGO_DB_NAME)
TASKS_COLLECTION = MONGO_CLIENT.collection(TASKS_COLLECTION_NAME)
THUMBNAILS_COLLECTION = MONGO_CLIENT.collection(THUMBNAILS_COLLECTION_NAME)


@app.get("/health", response_model=HealthStatus, status_code=status.HTTP_200_OK)
async def health_check():
    def instrument_disk_usage():
        stat = shutil.disk_usage(STORAGE_ROOT)
        percentage_used = round(stat[1] / stat[0], 2)
        disk_used.labels(disk_used).set(percentage_used)
        return percentage_used
    instrument_disk_usage()
    return JSONResponse({"status": "alive"})


@app.on_event("startup")
async def startup():
    Instrumentator().instrument(app).expose(app)


@app.get("/", status_code=status.HTTP_200_OK)
async def root() -> JSONResponse:
    response = {"message": f"Hello World!"}
    return JSONResponse(response)


@app.get("/tasks/{task_id}")
def get_status(task_id):
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    return JSONResponse(result)


@app.get("/thumbnail/", status_code=status.HTTP_200_OK)
async def get_thumbnail(task_id: str = Query(default=..., max_length=50),
                        response_model=ThumbnailResponse) -> JSONResponse:
    """GET the thumbnail download link by task id
    /thumbnail/?task_id=dasfsji12j3o12

    Args:
        task_id (str): thumbnail creation task_id 

    Returns:
        JSONResponse: json response
    """
    task_result = AsyncResult(task_id)
    if not task_result.successful():
        response.status_code = status.HTTP_400_BAD_REQUEST
        return JSONResponse({"message": f"Failed to get thumbnail: task status is not SUCCESS.",
                            "task_id": task_id, "status": task_result.status, "base64_thumbnail_data": ""})
    doc = TASKS_COLLECTION.find_one({"task_id": task_id})
    if not doc:
        response.status_code = status.HTTP_404_NOT_FOUND
        return JSONResponse({"message": f"Failed to get thumbnail: failed to find documents with associated task_id.",
                            "task_id": task_id, "status": task_result.status, "base64_thumbnail_data": ""})
    sha256 = doc["source_file_sha256"]
    doc = THUMBNAILS_COLLECTION.find_one({"source_file_sha256": sha256})
    response = {"message": "ok", "task_id": task_id,
                "status": task_result.status, "base64_thumbnail_data": doc["base64_thumbnail"]}
    return JSONResponse(response)


@app.post("/thumbnail/", response_model=ResponseMessage, status_code=status.HTTP_202_ACCEPTED)
async def create_thumbnail(thumbnail: ThumbnailRequestBody, response: Response) -> JSONResponse:
    """create a 100x100 thumbnail from an image

    Args:


    Returns:
        JSONResponse: json response
    """
    if not thumbnail.source_image_url:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return JSONResponse({"message": f"{thumbnail.source_image_url} source_image_url is empty."})
    if not validators.url(thumbnail.source_image_url):  # malformed url
        response.status_code = status.HTTP_400_BAD_REQUEST
        return JSONResponse({"message": f"{thumbnail.source_image_url} source_image_url is not an valid url."})
    source_file_name = os.path.basename(thumbnail.source_image_url)
    extension = source_file_name.split('.')[-1]
    if extension.lower() not in SUPPORTED_IMG_EXTENSIONS:
        response.status_code = status.HTTP_400_BAD_REQUEST
        resp_dict = {
            "message": f"{thumbnail.source_image_url} source_image_url is invalid: supported image extensions: {SUPPORTED_IMG_EXTENSIONS}."}
        return JSONResponse(resp_dict)
    storage_path = os.path.join(STORAGE_ROOT)
    logger.info(f"will save {source_file_name} to {storage_path}")
    task = resize_image_task.delay(source_image_url=thumbnail.source_image_url,
                                   storage_path=storage_path)
    response = {"task_id": task.id}
    return JSONResponse(response)
