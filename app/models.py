from pydantic import BaseModel


class ResponseMessage(BaseModel):
    task_id: str


class HealthStatus(BaseModel):
    status: str


class Thumbnail(BaseModel):
    source_image_url: str
    download_url: str
