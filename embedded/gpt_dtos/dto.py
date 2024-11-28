from pydantic import BaseModel


class ResponseFormat(BaseModel):
    in_phase: bool
    message: str
    quantity: int

class ResponseStopFormat(BaseModel):
    stop: bool
    message: str
    reason: str