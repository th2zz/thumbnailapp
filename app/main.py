# coding=utf-8

import datetime
import os

from fastapi import BackgroundTasks, FastAPI, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse

from app.utils import file_upload_task

app = FastAPI()
default_storage_dir = os.path.join("/tmp", "py_file_server_data")
os.makedirs(default_storage_dir, exist_ok=True)
STORAGE_ROOT = os.environ.get("STORAGE_ROOT", default_storage_dir)
FILE_READ_BATCH_SIZE = os.environ.get("FILE_READ_BATCH_SIZE", 100000)


@app.get("/")
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
async def download_file(name: str) -> FileResponse:
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


@app.post("/files/", status_code=status.HTTP_202_ACCEPTED)
async def upload_file(file: UploadFile, background_tasks: BackgroundTasks):
    """ upload a file by post. Content-Type: multipart/form-data

    Args:
        file: UploadFile a much faster mechanism from FastAPI for Content-Type: multipart/form-data
            https://fastapi.tiangolo.com/tutorial/request-files/#file-parameters-with-uploadfile

    Returns:
        dict: response message json
    """
    storage_path = os.path.join(STORAGE_ROOT, file.filename)
    background_tasks.add_task(file_upload_task, file_handle=file.file,
                              storage_path=storage_path, read_batch_size=FILE_READ_BATCH_SIZE)
    return {"message": f"{file.filename} upload task submitted."}


def get_app():
    return app
