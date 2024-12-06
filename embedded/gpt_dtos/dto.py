from pydantic import BaseModel


class Step(BaseModel):
    explanation: str
    output: str


class RegisterResponseFormat(BaseModel):
    message: str
    in_phase: bool
    firstname: str
    lastname: str


class ResponseFormat(BaseModel):
    in_phase: bool
    message: str
    quantity: int
    container: int
    want_to_register: bool


class ResponseStopFormat(BaseModel):
    stop: bool
    message: str
    reason: str
