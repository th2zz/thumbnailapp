from pydantic import BaseModel


class ResponseMessage(BaseModel):
    message: str


class HealthStatus(BaseModel):
    status: str
