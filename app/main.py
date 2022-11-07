# coding=utf-8

from celery import Celery
from fastapi import BackgroundTasks, FastAPI, UploadFile, status
from fastapi.responses import HTMLResponse

app = FastAPI()

REDIS_CONNECTION_STR = "redis://default:redispw@localhost:49154"
celery = Celery(
    __name__, broker=REDIS_CONNECTION_STR, backend=REDIS_CONNECTION_STR
)


@app.get("/")
async def root():
    content = """
<body>
<h1>File Upload</h1>
<form action="/files/" enctype="multipart/form-data" method="post">
<input name="file" type="file">
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)


@app.get("/files/{name}", status_code=status.HTTP_202_ACCEPTED)
def download_file(name: str):
    # GET the file with the given name
    return {}


@app.post("/files/", status_code=status.HTTP_202_ACCEPTED)
async def upload_file(file: UploadFile, background_tasks: BackgroundTasks):
    """

    Args:
        file: UploadFile a much faster mechanism from FastAPI
            https://fastapi.tiangolo.com/tutorial/request-files/#file-parameters-with-uploadfile

    Returns:

    """
    background_tasks.add_tasks(file_uploader)
    # Content-Type: multipart/form-data
    return {"filename": file.filename}


def file_uploader():
    pass


# @app.get('/blog/{id}', status_code=status.HTTP_200_OK)
# def get_blog(id: int, response: Response): < -- Add
#    if id > 3:
#         response.status_code = status.HTTP_404_NOT_FOUND
#         return {'error': f'Blog {id} not found'}
#     else:
#         response.status_code = status.HTTP_200_OK
#         return {'message': f'Blog {id} found'}
def get_app():
    return app
