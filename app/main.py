# coding=utf-8
import datetime
import logging.config
import os
import shutil

from fastapi import BackgroundTasks, FastAPI, Path, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from prometheus_client import Gauge
from prometheus_fastapi_instrumentator import Instrumentator

from app.models import HealthStatus, ResponseMessage
from app.utils import file_upload_task

CURR_FILE_PATH = os.path.abspath(__file__)
LOGGING_CONF_PATH = os.path.join(os.path.dirname(CURR_FILE_PATH),
                                 'logging.conf')
logging.config.fileConfig(LOGGING_CONF_PATH,
                          disable_existing_loggers=False)
# root level logger
logger = logging.getLogger(__name__)
default_storage_dir = os.path.join("/data", "simplefs_data")
os.makedirs(default_storage_dir, exist_ok=True)
STORAGE_ROOT = os.environ.get("STORAGE_ROOT", default_storage_dir)
FILE_READ_BATCH_SIZE = os.environ.get("FILE_READ_BATCH_SIZE", 100000)
DISK_USAGE_THRESHOLD = os.environ.get("DISK_USAGE_THRESHOLD", 95)
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


@app.get("/health", response_model=HealthStatus, status_code=status.HTTP_200_OK)
async def health_check():
    def instrument_disk_usage():
        stat = shutil.disk_usage(STORAGE_ROOT)
        percentage_used = round(stat[1] / stat[0], 2)
        disk_used.labels(disk_used).set(percentage_used)
        return percentage_used
    instrument_disk_usage()
    return {"status": "alive"}


@app.on_event("startup")
async def startup():
    Instrumentator().instrument(app).expose(app)


@app.get("/", status_code=status.HTTP_200_OK)
async def root() -> HTMLResponse:
    html_content = """
<body>
<h1>File Upload</h1>
<form action="/files/" enctype="multipart/form-data" method="post">
<input name="file" type="file">
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=html_content)


@app.get("/files/{name}", status_code=status.HTTP_200_OK)
async def download_file(name: str = Path(title="The name of the file to download")) -> FileResponse:
    """GET the file with the given name, asynchronously streams a file as the response.

    Args:
        name (str): file name

    Returns:
        FileResponse: https://fastapi.tiangolo.com/advanced/custom-response/#fileresponse
    """
    response = FileResponse(
        path=os.path.join(STORAGE_ROOT, name),
        filename=f"download_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{name}"
    )
    return response


@app.post("/files/", response_model=ResponseMessage, status_code=status.HTTP_202_ACCEPTED)
async def upload_file(file: UploadFile, background_tasks: BackgroundTasks):
    """ upload a file by post. Content-Type: multipart/form-data

    Args:
        file: UploadFile a much faster mechanism from FastAPI for Content-Type: multipart/form-data
            https://fastapi.tiangolo.com/tutorial/request-files/#file-parameters-with-uploadfile

    Returns:
        dict: response message json
    """
    storage_path = os.path.join(STORAGE_ROOT, file.filename)
    logger.info(f"saving file {storage_path}")
    background_tasks.add_task(file_upload_task, file_handle=file.file,
                              storage_path=storage_path, read_batch_size=FILE_READ_BATCH_SIZE)
    return {"message": f"{file.filename} upload task submitted."}
