from pydantic import BaseModel


class ResponseFormat(BaseModel):
    in_phase: bool
    message: str
    quantity: int
    want_to_register: bool

class ResponseStopFormat(BaseModel):
    stop: bool
    message: str
    reason: str