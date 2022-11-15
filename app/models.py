from pydantic import BaseModel


class ResponseMessage(BaseModel):
    task_id: str


class HealthStatus(BaseModel):
    status: str


class ThumbnailRequestBody(BaseModel):
    source_image_url: str


class ThumbnailResponse(BaseModel):
    message: str
    task_id: str
    celery_task_status: str  # refer to celery AsyncResult
    base64_thumbnail_data: str
